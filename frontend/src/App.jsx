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
    <TableContainer
      component={Paper}
      style={{
        fontSize: "12px"
      }}
    >
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell colSpan={3} style={{ padding: "6px 8px" }}>
              <strong>{table.label}</strong>
            </TableCell>
          </TableRow>

          <TableRow>
            <TableCell style={{ padding: "4px" }}>#</TableCell>
            <TableCell style={{ padding: "4px" }}>Team</TableCell>
            <TableCell align="right" style={{ padding: "4px" }}>
              {table.label}
            </TableCell>
          </TableRow>
        </TableHead>

        <TableBody>
          {table.rows.map((row, index) => (
            <TableRow
  key={index}
  style={{
    background:
      row.team.toLowerCase() === "rubber toe"
        ? "#fff3cd"   // yellow highlight
        : row.rank <= 3
        ? "#e6f4ea"   // top 3 green
        : row.rank >= table.rows.length - 2
        ? "#fdecea"   // bottom 3 red
        : "transparent",
    fontWeight:
      row.team.toLowerCase() === "rubber toe" ? "bold" : "normal"
  }}
>
              <TableCell style={{ padding: "4px" }}>{row.rank}</TableCell>
              <TableCell style={{ padding: "4px" }}>
                {row.team.slice(0, 12)} {/* shorten long names */}
              </TableCell>
              <TableCell align="right" style={{ padding: "4px" }}>
                {row.value}
              </TableCell>
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
         gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 12
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