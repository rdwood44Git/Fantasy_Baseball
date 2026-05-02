import { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  Paper
} from '@mui/material';

const hittingCategories = ["7", "12", "13", "16", "4"];
const pitchingCategories = ["28", "89", "42", "26", "27"];

function CategoryTable({ table }) {
  return (
    <TableContainer component={Paper} style={{ minWidth: 240 }}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell colSpan={3}>
              <strong>{table.label}</strong>
            </TableCell>
          </TableRow>

          <TableRow>
            <TableCell>Rank</TableCell>
            <TableCell>Team</TableCell>
            <TableCell align="right">{table.label}</TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {table.rows.map((row, index) => (
            <TableRow key={index}>
              <TableCell>{row.rank}</TableCell>
              <TableCell>{row.team}</TableCell>
              <TableCell align="right">{row.value}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function App() {
  const [categoryTables, setCategoryTables] = useState([]);

  useEffect(() => {
    fetch("https://fantasy-baseball-cmav.onrender.com/api/dashboard", {
      credentials: "include"
    })
      .then(res => res.json())
      .then(data => {
        console.log("Dashboard data:", data);
        setCategoryTables(data.categoryTables || []);
      })
      .catch(err => console.error(err));
  }, []);

  const hittingTables = hittingCategories
    .map(key => categoryTables.find(table => table.key === key))
    .filter(Boolean);

  const pitchingTables = pitchingCategories
    .map(key => categoryTables.find(table => table.key === key))
    .filter(Boolean);

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ textAlign: "center" }}>Fantasy Baseball Dashboard</h1>

      <h2>Hitting</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: 16,
          marginBottom: 32
        }}
      >
        {hittingTables.map(table => (
          <CategoryTable key={table.key} table={table} />
        ))}
      </div>

      <h2>Pitching</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          gap: 16
        }}
      >
        {pitchingTables.map(table => (
          <CategoryTable key={table.key} table={table} />
        ))}
      </div>
    </div>
  );
}

export default App;