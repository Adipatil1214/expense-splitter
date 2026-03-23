import { useEffect, useState } from "react";
import axios from "axios";

function Admin() {
  const [receipts, setReceipts] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchReceipts();
  }, []);

  const fetchReceipts = async () => {
    try {
      const res = await axios.get("http://localhost:5000/receipts");
      setReceipts(res.data.receipts);
    } catch (error) {
      setMessage("Error fetching receipts.");
    }
  };

  const approveReceipt = async (id) => {
    try {
      const res = await axios.post(`http://localhost:5000/approve/${id}`);
      setMessage(res.data.message || "Receipt approved!");
      fetchReceipts();
    } catch (err) {
      setMessage("Error approving receipt.");
    }
  };

  const addVendor = async (id) => {
    try {
      const res = await axios.post(`http://localhost:5000/add-vendor/${id}`);
      setMessage(res.data.message || "Vendor added to database!");
      fetchReceipts();
    } catch (err) {
      setMessage("Error adding vendor.");
    }
  };

  const viewReceipt = (imagePath) => {
    window.open(`http://localhost:5000/${imagePath}`, "_blank");
  };
  const deleteReceipt = async (id) => {
    try {
      const res = await axios.delete(`http://localhost:5000/delete/${id}`);
      
      setMessage(res.data.message || "Receipt deleted!");
      fetchReceipts();
    } catch (err) {
      setMessage("Error deleting receipt.");
    }
  };

  const exportExcel = () => {
    window.open("http://localhost:5000/export", "_blank");
  };  

  return (
    <div style={{ padding: "20px" }}>
      <h2>Admin Panel</h2>
      <button onClick={exportExcel} style={{ marginBottom: "15px" }}>Export to Excel</button>
      {/* Feedback message */}
      {message && (
        <div style={{ color: "green", marginBottom: "15px" }}>{message}</div>
      )}

      <table border="1" cellPadding="10">
        <thead>
          <tr>
            <th>ID</th>
            <th>User</th>
            <th>Vendor</th>
            <th>Status</th>
            <th>Amount</th>
            <th>Date</th>
            <th>Actions</th>
            <th>View Receipt</th>
          </tr>
        </thead>

        <tbody>
          {receipts.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.user_id}</td>
              <td>{r.vendor_name}</td>
              <td>{r.status}</td>
              <td>{r.amount ? `₹${r.amount}` : "Not detected"}</td>
              <td>{r.receipt_date}</td>

              {/* Actions */}
              <td>
                {r.status === "PENDING" && (
                  <button onClick={() => approveReceipt(r.id)}>Approve</button>
                )}

                {r.status === "APPROVED" && (
                  <button onClick={() => addVendor(r.id)}>Add to DB</button>
                )}

                <button
                  style={{ marginLeft: "10px", color: "red" }}
                  onClick={() => deleteReceipt(r.id)}
                >
                  Delete
                </button>
              </td>

              {/* View Receipt */}
              <td>
                <button onClick={() => viewReceipt(r.image_path)}>View</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Admin;
