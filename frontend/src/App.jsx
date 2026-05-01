import { useEffect, useState } from 'react';
import {
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  Paper
} from '@mui/material';

function App() {
  const [teams, setTeams] = useState([]);

  useEffect(() => {
    fetch("https://fantasy-baseball-cmav.onrender.com/api/dashboard", {
  credentials: "include"
})
      .then(res => res.json())
      .then(data => {
           console.log("Dashboard data:", data);
           setTeams(data.teams || []);
          })
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Fantasy Baseball Dashboard</h1>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Team</TableCell>
              <TableCell>Wins</TableCell>
              <TableCell>Losses</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {teams.map((team, index) => (
              <TableRow key={index}>
                <TableCell>{team.name}</TableCell>
                <TableCell>{team.wins}</TableCell>
                <TableCell>{team.losses}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

export default App;