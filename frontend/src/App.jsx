import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8080";

function formatValue(value, key) {
  if (value === null || value === undefined || value === "") return "";

  const lowerKey = key?.toLowerCase() || "";

  if (
    lowerKey.includes("obp") ||
    lowerKey.includes("woba") ||
    lowerKey.includes("era") ||
    lowerKey.includes("whip")
  ) {
    const num = Number(value);
    return Number.isNaN(num) ? value : num.toFixed(3);
  }

  return value;
}

function sortRows(rows, sortKey, sortDir) {
  return [...rows].sort((a, b) => {
    const av = a[sortKey] ?? "";
    const bv = b[sortKey] ?? "";

    const aNum = Number(av);
    const bNum = Number(bv);

    if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) {
      return sortDir === "asc" ? aNum - bNum : bNum - aNum;
    }

    return sortDir === "asc"
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });
}

function TeamAveragesTable({ rows, type, setType, week, setWeek }) {
  const [sortKey, setSortKey] = useState(
    type === "hitters" ? "r_weekly" : "k_weekly"
  );
  const [sortDir, setSortDir] = useState("desc");

  const isAverage = week === "average";

  const hitterColumns = [
    { key: "fantasy_team_name", label: "Fantasy Team" },
    ...(isAverage ? [{ key: "starters_count", label: "Starters" }] : []),
    { key: "r_weekly", label: isAverage ? "R/Wk" : "R" },
    { key: "hr_weekly", label: isAverage ? "HR/Wk" : "HR" },
    { key: "rbi_weekly", label: isAverage ? "RBI/Wk" : "RBI" },
    { key: "sb_weekly", label: isAverage ? "SB/Wk" : "SB" },
    { key: "obp_avg", label: "OBP" },
  ];

  const pitcherColumns = [
    { key: "fantasy_team_name", label: "Fantasy Team" },
    ...(isAverage ? [{ key: "starters_count", label: "Pitchers" }] : []),
    { key: "w_weekly", label: isAverage ? "W/Wk" : "W" },
    { key: "k_weekly", label: isAverage ? "K/Wk" : "K" },
    { key: "sv_hld_weekly", label: isAverage ? "SV+H/Wk" : "SV+H" },
    { key: "era_avg", label: "ERA" },
    { key: "whip_avg", label: "WHIP" },
  ];

  const columns = type === "hitters" ? hitterColumns : pitcherColumns;

  const sortedRows = useMemo(
    () => sortRows(rows, sortKey, sortDir),
    [rows, sortKey, sortDir]
  );

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <section className="stat-section summary-section">
      <div className="section-title-row">
        <div className="section-title-left">
          <div className="section-icon">📊</div>
          <div>
            <h2>Team Category Summary</h2>
            <p>Weekly category averages by fantasy team</p>
          </div>
        </div>
      </div>

      <div className="stat-toolbar compact-toolbar">
        <select
          value={type}
          onChange={(e) => {
            const newType = e.target.value;
            setType(newType);
            setSortKey(newType === "hitters" ? "r_weekly" : "k_weekly");
            setSortDir("desc");
          }}
        >
          <option value="hitters">Hitters</option>
          <option value="pitchers">Pitchers</option>
        </select>

        <select
          value={week}
          onChange={(e) => {
            setWeek(e.target.value);
          }}
        >
          <option value="average">Weekly Averages</option>
          {Array.from({ length: 25 }, (_, i) => (
            <option key={i + 1} value={String(i + 1)}>
              Week {i + 1}
            </option>
          ))}
        </select>
      </div>

      <div className="table-scroll small-table-scroll">
        <table className="stat-table">
          <thead>
            <tr>
              <th>Rk.</th>
              {columns.map((col) => (
                <th key={col.key} onClick={() => handleSort(col.key)}>
                  {col.label}
                  {sortKey === col.key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {sortedRows.map((row, index) => (
              <tr key={row.fantasy_team_name}>
                <td>{index + 1}</td>
                {columns.map((col) => (
                  <td key={col.key}>{formatValue(row[col.key], col.key)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function PlayerTable({
  title,
  rows,
  columns,
  columnGroups,
  defaultSortKey,
  defaultSortDir = "asc",
  icon = "⚾",
  subtitle = "Advanced player analytics",
}) {
  const [search, setSearch] = useState("");
  const [ownership, setOwnership] = useState("all");
  const [positionFilter, setPositionFilter] = useState("all");
  const [sortKey, setSortKey] = useState(defaultSortKey || columns[0].key);
  const [sortDir, setSortDir] = useState(defaultSortDir);
  const [pageSize, setPageSize] = useState(50);
  const [page, setPage] = useState(1);
  const [compareIds, setCompareIds] = useState([]);
  const [showCompareOnly, setShowCompareOnly] = useState(false);

  const cleanRows = useMemo(() => {
    const seen = new Map();

    rows.forEach((p) => {
      const key =
        p.yahoo_player_id ||
        `${p.yahoo_name || ""}-${p.yahoo_team || ""}-${p.player_type || ""}`;

      if (!seen.has(key)) {
        seen.set(key, {
          ...p,
          _compareKey: key,
        });
      }
    });

    return Array.from(seen.values());
  }, [rows]);

  const positionOptions = useMemo(() => {
    const positions = new Set();

    cleanRows.forEach((p) => {
      String(p.yahoo_positions || "")
        .split(",")
        .map((pos) => pos.trim())
        .filter(Boolean)
        .forEach((pos) => positions.add(pos));
    });

    return Array.from(positions).sort();
  }, [cleanRows]);

  function toggleCompare(playerKey) {
    setCompareIds((current) =>
      current.includes(playerKey)
        ? current.filter((id) => id !== playerKey)
        : [...current, playerKey]
    );
  }

  const filteredRows = useMemo(() => {
    let result = [...cleanRows];

    if (search) {
      const s = search.toLowerCase();

      result = result.filter(
        (p) =>
          p.yahoo_name?.toLowerCase().includes(s) ||
          p.yahoo_team?.toLowerCase().includes(s) ||
          p.fantasy_team_name?.toLowerCase().includes(s)
      );
    }

    if (ownership === "available") {
      result = result.filter((p) => p.is_available === 1);
    }

    if (ownership === "mine") {
      result = result.filter((p) => p.is_on_my_team === 1);
    }

    if (ownership === "rostered") {
      result = result.filter((p) => p.fantasy_team_name);
    }

    if (positionFilter !== "all") {
      result = result.filter((p) =>
        String(p.yahoo_positions || "")
          .split(",")
          .map((pos) => pos.trim())
          .includes(positionFilter)
      );
    }

    if (showCompareOnly) {
      result = result.filter((p) => compareIds.includes(p._compareKey));
    }

    return sortRows(result, sortKey, sortDir);
  }, [
    cleanRows,
    search,
    ownership,
    positionFilter,
    sortKey,
    sortDir,
    compareIds,
    showCompareOnly,
  ]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const safePage = Math.min(page, totalPages);

  const visibleRows = filteredRows.slice(
    (safePage - 1) * pageSize,
    safePage * pageSize
  );

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <section className="stat-section player-card">
      <div className="player-dashboard-titlebar">
        <div className="dashboard-title-left">
          <div className="dashboard-icon">{icon}</div>
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>
        </div>

        <div className="dashboard-controls">
          <div className="search-box">
            <span>⌕</span>
            <input
              placeholder="Search player, team, or owner..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>

          <select
            value={ownership}
            onChange={(e) => {
              setOwnership(e.target.value);
              setPage(1);
            }}
          >
            <option value="all">All Ownership</option>
            <option value="available">Available</option>
            <option value="mine">My Team</option>
            <option value="rostered">Rostered</option>
          </select>

          <select
            value={positionFilter}
            onChange={(e) => {
              setPositionFilter(e.target.value);
              setPage(1);
            }}
          >
            <option value="all">All Positions</option>
            {positionOptions.map((pos) => (
              <option key={pos} value={pos}>
                {pos}
              </option>
            ))}
          </select>

          <label className="compare-toggle modern-toggle">
            <input
              type="checkbox"
              checked={showCompareOnly}
              onChange={(e) => {
                setShowCompareOnly(e.target.checked);
                setPage(1);
              }}
            />
            Compare Only
          </label>

          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setCompareIds([]);
              setShowCompareOnly(false);
              setPage(1);
            }}
          >
            Clear Compare
          </button>
        </div>
      </div>

      <div className="table-scroll player-table-scroll">
        <table className="stat-table player-table">
          <thead>
            <tr className="category-row">
              <th rowSpan="2" className="sticky-compare">
                <input
                  type="checkbox"
                  checked={
                    visibleRows.length > 0 &&
                    visibleRows.every((p) => compareIds.includes(p._compareKey))
                  }
                  onChange={(e) => {
                    if (e.target.checked) {
                      setCompareIds((current) => [
                        ...new Set([
                          ...current,
                          ...visibleRows.map((p) => p._compareKey),
                        ]),
                      ]);
                    } else {
                      setCompareIds((current) =>
                        current.filter(
                          (id) => !visibleRows.some((p) => p._compareKey === id)
                        )
                      );
                    }
                  }}
                />
              </th>
              <th rowSpan="2" className="sticky-rank">
                Rk.
              </th>

              {columnGroups.map((group, index) => (
                <th
                  key={`${group.label || "blank"}-${index}`}
                  colSpan={group.colSpan}
                >
                  {group.label}
                </th>
              ))}
            </tr>

            <tr className="subheader-row">
              {columns.map((col, index) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  className={[
                    index === 0 ? "sticky-player-header" : "",
                    col.groupStart ? "group-start" : "",
                  ].join(" ")}
                >
                  {col.label}
                  {sortKey === col.key ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {visibleRows.map((p, index) => (
              <tr key={p._compareKey}>
                <td className="sticky-compare">
                  <input
                    type="checkbox"
                    checked={compareIds.includes(p._compareKey)}
                    onChange={() => toggleCompare(p._compareKey)}
                  />
                </td>

                <td className="sticky-rank">
                  {(safePage - 1) * pageSize + index + 1}
                </td>

                {columns.map((col, colIndex) => (
                  <td
                    key={col.key}
                    className={[
                      colIndex === 0 ? "sticky-player-cell" : "",
                      col.groupStart ? "group-start" : "",
                    ].join(" ")}
                  >
                    {col.key === "injury_status" ? (
                      <span
                        className={[
                          "status-pill",
                          p.injury_status ? "status-alert" : "status-active",
                          p.injury_status === "NA" ? "status-na" : "",
                          p.injury_status?.startsWith("IL") ? "status-il" : "",
                          p.injury_status === "DTD" ? "status-dtd" : "",
                        ].join(" ")}
                      >
                        {p.injury_status || "Active"}
                      </span>
                    ) : col.key === "yahoo_name" ? (
                      <span className="player-name-text">
                        {formatValue(p[col.key], col.key)}
                      </span>
                    ) : (
                      formatValue(p[col.key], col.key)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination commercial-pagination">
        <span>
          Showing {(safePage - 1) * pageSize + 1} to {Math.min(safePage * pageSize, filteredRows.length)} of {filteredRows.length} players
        </span>

        <div className="pagination-buttons">
          <button disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>
            ‹
          </button>
          <strong>{safePage}</strong>
          <button
            disabled={safePage >= totalPages}
            onClick={() => setPage(safePage + 1)}
          >
            ›
          </button>
        </div>

        <label className="rows-per-page">
          Rows per page:
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
          >
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={250}>250</option>
          </select>
        </label>
      </div>
    </section>
  );
}

function App() {
  const [data, setData] = useState({ hitters: [], pitchers: [] });
  const [teamAverages, setTeamAverages] = useState([]);
  const [teamType, setTeamType] = useState("hitters");
  const [teamWeek, setTeamWeek] = useState("average");

  useEffect(() => {
    fetch(`${API_BASE}/api/player-category-summary`)
      .then((res) => res.json())
      .then(setData)
      .catch(console.error);
  }, []);

  useEffect(() => {
    fetch(
      `${API_BASE}/api/team-weekly-averages?type=${teamType}&week=${teamWeek}`
    )
      .then((res) => res.json())
      .then(setTeamAverages)
      .catch(console.error);
  }, [teamType, teamWeek]);

  const hitterColumns = [
    { key: "yahoo_name", label: "Player" },
    { key: "yahoo_team", label: "MLB" },
    { key: "yahoo_positions", label: "Pos" },
    { key: "injury_status", label: "Status" },
    { key: "fantasy_team_name", label: "Fantasy Team" },

    { key: "yahoo_hitter_season_rank", label: "All", groupStart: true },
    { key: "yahoo_hitter_30_day_rank", label: "30d" },

    { key: "active_r_weekly", label: "Active", groupStart: true },
    { key: "projected_r_weekly", label: "ROS" },

    { key: "active_hr_weekly", label: "Active", groupStart: true },
    { key: "projected_hr_weekly", label: "ROS" },

    { key: "active_rbi_weekly", label: "Active", groupStart: true },
    { key: "projected_rbi_weekly", label: "ROS" },

    { key: "active_sb_weekly", label: "Active", groupStart: true },
    { key: "projected_sb_weekly", label: "ROS" },

    { key: "active_obp", label: "Active", groupStart: true },
    { key: "projected_obp_weekly", label: "ROS" },

    { key: "availability_pct", label: "%", groupStart: true },

    { key: "hitter_xwoba_14", label: "14", groupStart: true },
    { key: "hitter_xwoba_30", label: "30" },
    { key: "hitter_xwoba_season", label: "Season" },

    { key: "hitter_woba_14", label: "14", groupStart: true },
    { key: "hitter_woba_30", label: "30" },
    { key: "hitter_woba_season", label: "Season" },
  ];

  const hitterGroups = [
    { label: "", colSpan: 5 },
    { label: "Yahoo Rank", colSpan: 2 },
    { label: "Runs Weekly", colSpan: 2 },
    { label: "HR Weekly", colSpan: 2 },
    { label: "RBI Weekly", colSpan: 2 },
    { label: "SB Weekly", colSpan: 2 },
    { label: "OBP", colSpan: 2 },
    { label: "Avail", colSpan: 1 },
    { label: "xwOBA", colSpan: 3 },
    { label: "wOBA", colSpan: 3 },
  ];

  const pitcherColumns = [
    { key: "yahoo_name", label: "Player" },
    { key: "yahoo_team", label: "MLB" },
    { key: "yahoo_positions", label: "Pos" },
    { key: "injury_status", label: "Status" },
    { key: "fantasy_team_name", label: "Fantasy Team" },

    { key: "yahoo_pitcher_season_rank", label: "All", groupStart: true },
    { key: "yahoo_pitcher_30_day_rank", label: "30d" },

    { key: "active_w_weekly", label: "Active", groupStart: true },
    { key: "projected_w_weekly", label: "ROS" },

    { key: "active_k_weekly", label: "Active", groupStart: true },
    { key: "projected_k_weekly", label: "ROS" },

    { key: "active_sv_hld_weekly", label: "Active", groupStart: true },
    { key: "projected_sv_hld_weekly", label: "ROS" },

    { key: "active_era", label: "Active", groupStart: true },
    { key: "projected_era_weekly", label: "ROS" },

    { key: "active_whip", label: "Active", groupStart: true },
    { key: "projected_whip_weekly", label: "ROS" },

    { key: "availability_pct", label: "%", groupStart: true },

    { key: "pitcher_xwoba_against_14", label: "14", groupStart: true },
    { key: "pitcher_xwoba_against_30", label: "30" },
    { key: "pitcher_xwoba_against_season", label: "Season" },

    { key: "pitcher_woba_against_14", label: "14", groupStart: true },
    { key: "pitcher_woba_against_30", label: "30" },
    { key: "pitcher_woba_against_season", label: "Season" },
  ];

  const pitcherGroups = [
    { label: "", colSpan: 5 },
    { label: "Yahoo Rank", colSpan: 2 },
    { label: "Wins Weekly", colSpan: 2 },
    { label: "Strikeouts Weekly", colSpan: 2 },
    { label: "SV+H Weekly", colSpan: 2 },
    { label: "ERA", colSpan: 2 },
    { label: "WHIP", colSpan: 2 },
    { label: "Avail", colSpan: 1 },
    { label: "xwOBA Against", colSpan: 3 },
    { label: "wOBA Against", colSpan: 3 },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-brand">
          <div className="baseball-logo">⚾</div>

          <div>
            <h1>Millie's Fantasy Baseball</h1>
            <p>Advanced Player Analytics Dashboard</p>
          </div>
        </div>

        <div className="app-season">
          <div>Week 15</div>
          <span>2026 Season</span>
        </div>
      </header>

      <TeamAveragesTable
        rows={teamAverages}
        type={teamType}
        setType={setTeamType}
        week={teamWeek}
        setWeek={setTeamWeek}
      />

      <PlayerTable
        title="Hitters Dashboard"
        icon="⚾"
        subtitle="Advanced player analytics"
        rows={data.hitters}
        columns={hitterColumns}
        columnGroups={hitterGroups}
        defaultSortKey="yahoo_hitter_season_rank"
        defaultSortDir="asc"
      />

      <PlayerTable
        title="Pitchers Dashboard"
        icon="⚾"
        subtitle="Pitching performance analytics"
        rows={data.pitchers}
        columns={pitcherColumns}
        columnGroups={pitcherGroups}
        defaultSortKey="yahoo_pitcher_season_rank"
        defaultSortDir="asc"
      />
    </div>
  );
}

export default App;
