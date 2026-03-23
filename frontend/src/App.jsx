import { useState } from "react";
import axios from "axios";
import Admin from "./Admin.jsx";

function App() {
  const [file, setFile] = useState(null);
  const [userId, setUserId] = useState("");
  const [receiptDate, setReceiptDate] = useState("");
  const [useToday, setUseToday] = useState(false);
  const [result, setResult] = useState(null);
  const [showAdmin, setShowAdmin] = useState(false);

  const handleUpload = async () => {
    const formData = new FormData();

    formData.append("receipt", file);
    formData.append("user_id", userId);

    const finalDate = useToday
      ? new Date().toISOString().split("T")[0]
      : receiptDate;

    formData.append("receipt_date", finalDate);

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

          {/* USER ID */}
          <input
            type="text"
            placeholder="Enter User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />

          <br /><br />

          {/* DATE INPUT */}
          <input
            type="date"
            value={receiptDate}
            onChange={(e) => setReceiptDate(e.target.value)}
            disabled={useToday}
          />

          <br />

          {/* ✅ UPDATED CHECKBOX */}
          <label>
            <input
              type="checkbox"
              checked={useToday}
              onChange={() => {
                const newVal = !useToday;
                setUseToday(newVal);

                if (newVal) {
                  setReceiptDate(new Date().toISOString().split("T")[0]);
                }
              }}
            />
            Use Current Date
          </label>

          <br /><br />

          {/* FILE INPUT */}
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
          />

          <br /><br />

          <button onClick={handleUpload}>Upload</button>

          {result && (
            <div>
              <h3>Vendor: {result.vendor}</h3>
              <h3>Amount: {result.amount}</h3>
              <h3>Status: {result.status}</h3>
              <h3>Date: {result.receipt_date}</h3>
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