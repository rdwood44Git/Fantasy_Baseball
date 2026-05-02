import { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  Paper
} from '@mui/material';

console.log("VITE CONFIG LOADED")

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

  return (
    <div style={{ padding: 20 }}>
      <h1>Fantasy Baseball Dashboard</h1>

      {categoryTables.map((table) => (
        <TableContainer
          component={Paper}
          key={table.key}
          style={{ marginBottom: 24 }}
        >
          <Table>
            <TableHead>
              <TableRow>
                <TableCell colSpan={3}>
                  <strong>{table.label}</strong>
                </TableCell>
              </TableRow>

              <TableRow>
                <TableCell>Rank</TableCell>
                <TableCell>Team</TableCell>
                <TableCell align="right">{table.key}</TableCell>
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
      ))}
    </div>
  );
}

export default App;