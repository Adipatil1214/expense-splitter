import { useState } from "react";
import axios from "axios";
import Admin from "./admin.jsx"

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [showAdmin, setShowAdmin] = useState(false);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("receipt", file);

    const res = await axios.post(
      "http://localhost:5000/upload",
      formData
    );

    setResult(res.data);
  };

  return (
    <div style={{ padding: "40px" }}>
      <h2>Receipt Verification System</h2>

      <button onClick={() => setShowAdmin(!showAdmin)}>
        {showAdmin ? "Back to Upload" : "Go to Admin Panel"}
      </button>

      <br /><br />

      {!showAdmin ? (
        <div>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
          />

          <br /><br />

          <button onClick={handleUpload}>Upload</button>

          {result && (
            <div>
              <h3>Vendor: {result.vendor}</h3>
              <h3>Status: {result.status}</h3>
            </div>
          )}
        </div>
      ) : (
        <Admin />
      )}
    </div>
  );
}

export default App;