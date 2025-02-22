import os
import asyncio
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify your frontend URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded files
UPLOAD_DIR = "uploaded_files"
RESULT_DIR = "result_files"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Helper functions (add your genome assembly functions here)

def preprocess_reads(file_path: str) -> List[str]:
    with open(file_path, "r") as file:
        lines = file.readlines()
    reads = [line.strip() for line in lines if not line.startswith(">")]
    return reads

def classify_reads_by_length(reads: List[str], threshold: int = 1000):
    short_reads = [read for read in reads if len(read) < threshold]
    long_reads = [read for read in reads if len(read) >= threshold]
    return short_reads, long_reads

def dynamic_kmer_selection(reads: List[str]) -> int:
    avg_length = sum(len(read) for read in reads) // len(reads)
    return max(15, min(31, avg_length // 2))

def generate_kmers(reads: List[str], k: int) -> List[str]:
    kmers = []
    for read in reads:
        for i in range(len(read) - k + 1):
            kmers.append(read[i:i + k])
    return kmers

def filter_low_frequency_kmers(kmers: List[str], threshold: int = 2) -> List[str]:
    from collections import Counter
    kmer_counts = Counter(kmers)
    return [k for k in kmers if kmer_counts[k] >= threshold]

def construct_de_bruijn_graph(kmers: List[str]):
    import networkx as nx
    G = nx.DiGraph()
    for kmer in kmers:
        prefix, suffix = kmer[:-1], kmer[1:]
        G.add_edge(prefix, suffix)
    return G

def find_eulerian_path(G):
    import networkx as nx
    if nx.is_eulerian(G):
        return list(nx.eulerian_path(G))
    return []

def scaffold_with_long_reads(assembled_sequence, long_reads):
    scaffolds = assembled_sequence.copy()
    for long_read in long_reads:
        i = 0
        while i < len(scaffolds) - 1:
            if scaffolds[i] in long_read and scaffolds[i + 1] in long_read:
                scaffolds[i] += "N" * 10 + scaffolds[i + 1]
                scaffolds.pop(i + 1)
            else:
                i += 1
    return scaffolds

def save_result(scaffolds, filename="assembled_genome.txt"):
    result_path = os.path.join(RESULT_DIR, filename)
    with open(result_path, "w") as f:
        for scaffold in scaffolds:
            f.write(scaffold + "\n")
    return result_path

@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save the uploaded file
    with open(file_location, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            f.write(chunk)

    try:
        # Process the file
        reads = await asyncio.to_thread(preprocess_reads, file_location)
        short_reads, long_reads = classify_reads_by_length(reads)
        k = dynamic_kmer_selection(short_reads + long_reads)
        kmers = generate_kmers(short_reads + long_reads, k)
        kmers = filter_low_frequency_kmers(kmers)

        G = construct_de_bruijn_graph(kmers)
        assembled_sequence = find_eulerian_path(G)
        assembled_sequence = [edge[0] for edge in assembled_sequence]

        scaffolds = scaffold_with_long_reads(assembled_sequence, long_reads)

        result_filename = "assembled_genome.txt"
        result_path = save_result(scaffolds, result_filename)

        return {"filename": result_filename, "file_url": f"/download/{result_filename}"}

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="File processing error")

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

