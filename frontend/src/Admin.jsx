import { useEffect, useState } from "react";
import axios from "axios";

function Admin() {
  const [receipts, setReceipts] = useState([]);

  useEffect(() => {
    fetchReceipts();
  }, []);

  const fetchReceipts = async () => {
    const res = await axios.get("http://localhost:5000/receipts");
    setReceipts(res.data.receipts);
  };

  // const approve = async (id) => {
  //   await axios.post(`http://localhost:5000/approve/${id}`);
  //   fetchReceipts();
  // };
  const approveVendor = async (id) => {
  await axios.post(`http://localhost:5000/approve-vendor/${id}`);
  fetchReceipts();
  };
  return (
    <div>
      <h2>Admin Panel</h2>
      <table border="1">
        <thead>
          <tr>
            <th>ID</th>
            <th>Vendor</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {receipts.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.vendor_name}</td>
              <td>{r.status}</td>
              <td>{r.status === "PENDING" && (
              <button onClick={() => approveVendor(r.id)}>Approve Vendor</button>)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Admin;