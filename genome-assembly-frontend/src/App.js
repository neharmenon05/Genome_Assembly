import React, { useState } from "react";
import axios from "axios";
import { Button, CircularProgress, Typography, Box, TextField } from "@mui/material";

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const result = await axios.post("http://127.0.0.1:8000/uploadfile/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setResponse(result.data);
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = () => {
    if (response && response.file_url) {
      window.location.href = `http://127.0.0.1:8000${response.file_url}`;
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", padding: 2 }}>
      <Typography variant="h3" gutterBottom>
        Genome Assembly Tool
      </Typography>
      <form onSubmit={handleSubmit} style={{ width: "100%", maxWidth: "500px" }}>
        <TextField
          fullWidth
          variant="outlined"
          type="file"
          onChange={handleFileChange}
          sx={{ marginBottom: 2 }}
        />
        <Button
          variant="contained"
          color="primary"
          type="submit"
          fullWidth
          disabled={loading}
          sx={{ marginBottom: 2 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : "Upload File"}
        </Button>
      </form>

      {loading && <Typography variant="body1">Processing file... Please wait.</Typography>}

      {response && (
        <Box sx={{ textAlign: "center", marginTop: 3 }}>
          <Typography variant="h5">Processing Complete!</Typography>
          <Typography variant="body1">
            Your assembled genome is ready for download.
          </Typography>
          <Button variant="contained" color="success" onClick={downloadFile}>
            Download Genome
          </Button>
        </Box>
      )}
    </Box>
  );
}

export default App;
