import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Cpu,
  Database,
  RefreshCw,
  Search,
  Server,
  Workflow,
  XCircle,
} from "lucide-react";

import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [jobs, setJobs] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  async function loadData() {
    try {
      const [metricsResponse, jobsResponse] = await Promise.all([
        axios.get(`${API_URL}/metrics`),
        axios.get(`${API_URL}/jobs`),
      ]);

      setMetrics(metricsResponse.data);
      setJobs(jobsResponse.data);
      setLastUpdated(new Date());
    } catch (error) {
      console.error("Failed to load JobFlow data:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();

    const interval = setInterval(loadData, 3000);

    return () => clearInterval(interval);
  }, []);

  const retrying = jobs.filter(
    (job) =>
      job.status === "scheduled" &&
      job.retry_count > 0
  ).length;

  const activeWorkers = new Set(
    jobs
      .filter(
        (job) =>
          job.status === "running" &&
          job.worker_id
      )
      .map((job) => job.worker_id)
  ).size;

  const filteredJobs = useMemo(() => {
    return jobs.filter((job) => {
      const matchesSearch =
        job.job_type
          ?.toLowerCase()
          .includes(search.toLowerCase()) ||
        String(job.id).includes(search) ||
        job.worker_id
          ?.toLowerCase()
          .includes(search.toLowerCase());

      let matchesStatus = true;

      if (statusFilter !== "all") {
        if (statusFilter === "retrying") {
          matchesStatus =
            job.status === "scheduled" &&
            job.retry_count > 0;
        } else {
          matchesStatus =
            job.status === statusFilter;
        }
      }

      return matchesSearch && matchesStatus;
    });
  }, [jobs, search, statusFilter]);

  const statCards = [
    {
      title: "Queued",
      value: metrics.queued ?? 0,
      description: "Waiting for workers",
      icon: Clock3,
      className: "queued",
    },
    {
      title: "Running",
      value: metrics.running ?? 0,
      description: "Currently processing",
      icon: Activity,
      className: "running",
    },
    {
      title: "Retrying",
      value: retrying,
      description: "Waiting on backoff",
      icon: RefreshCw,
      className: "retrying",
    },
    {
      title: "Dead",
      value: metrics.dead ?? 0,
      description: "Retries exhausted",
      icon: AlertTriangle,
      className: "dead",
    },
  ];

  return (
    <div className="app">
      <div className="background-glow glow-one" />
      <div className="background-glow glow-two" />

      <main className="dashboard">
        <header className="topbar">
          <div className="brand">
            <div className="brand-icon">
              <Workflow size={25} />
            </div>

            <div>
              <div className="brand-row">
                <h1>JobFlow</h1>
                <span className="version">v0.1</span>
              </div>

              <p>
                Distributed Job & Workflow
                Orchestration Engine
              </p>
            </div>
          </div>

          <div className="header-actions">
            <div className="worker-indicator">
              <span className="online-dot" />

              <div>
                <strong>{activeWorkers}</strong>
                <span>
                  Active Worker
                  {activeWorkers === 1 ? "" : "s"}
                </span>
              </div>
            </div>

            <button
              className="refresh-button"
              onClick={loadData}
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
        </header>

        <div className="system-strip">
          <div>
            <Database size={15} />
            <span>PostgreSQL</span>
          </div>

          <span className="system-arrow">→</span>

          <div>
            <Server size={15} />
            <span>Job Queue</span>
          </div>

          <span className="system-arrow">→</span>

          <div>
            <Cpu size={15} />
            <span>Worker Pool</span>
          </div>

          <div className="system-status">
            <span className="online-dot" />
            System operational
          </div>
        </div>

        <section className="stats-grid">
          {statCards.map((card) => {
            const Icon = card.icon;

            return (
              <article
                key={card.title}
                className={`stat-card ${card.className}`}
              >
                <div className="stat-top">
                  <span className="stat-title">
                    {card.title}
                  </span>

                  <div className="stat-icon">
                    <Icon size={19} />
                  </div>
                </div>

                <div className="stat-value">
                  {card.value}
                </div>

                <div className="stat-footer">
                  <span className="mini-dot" />
                  {card.description}
                </div>
              </article>
            );
          })}
        </section>

        <section className="jobs-panel">
          <div className="jobs-header">
            <div>
              <div className="section-title-row">
                <h2>Jobs</h2>

                <span className="job-count">
                  {jobs.length}
                </span>
              </div>

              <p>
                Live execution activity across your
                worker pool
              </p>
            </div>

            <div className="job-controls">
              <div className="search-box">
                <Search size={17} />

                <input
                  type="text"
                  placeholder="Search jobs..."
                  value={search}
                  onChange={(event) =>
                    setSearch(event.target.value)
                  }
                />
              </div>

              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(
                    event.target.value
                  )
                }
              >
                <option value="all">
                  All statuses
                </option>

                <option value="queued">
                  Queued
                </option>

                <option value="running">
                  Running
                </option>

                <option value="succeeded">
                  Succeeded
                </option>

                <option value="retrying">
                  Retrying
                </option>

                <option value="dead">
                  Dead
                </option>
              </select>
            </div>
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Job Type</th>
                  <th>Status</th>
                  <th>Worker</th>
                  <th>Priority</th>
                  <th>Attempts</th>
                  <th>Retries</th>
                </tr>
              </thead>

              <tbody>
                {filteredJobs.map((job) => (
                  <JobRow
                    key={job.id}
                    job={job}
                  />
                ))}
              </tbody>
            </table>

            {!loading &&
              filteredJobs.length === 0 && (
                <div className="empty-state">
                  <Database size={28} />

                  <strong>No jobs found</strong>

                  <span>
                    New jobs will appear here
                    automatically.
                  </span>
                </div>
              )}

            {loading && (
              <div className="empty-state">
                <RefreshCw
                  size={25}
                  className="spin"
                />

                <strong>
                  Loading JobFlow...
                </strong>
              </div>
            )}
          </div>

          <div className="table-footer">
            <span>
              Showing {filteredJobs.length} of{" "}
              {jobs.length} jobs
            </span>

            <span>
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()}`
                : "Connecting..."}
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}

function JobRow({ job }) {
  const statusInfo = getStatusInfo(job);

  const StatusIcon = statusInfo.icon;

  return (
    <tr>
      <td>
        <span className="job-id">
          #{job.id}
        </span>
      </td>

      <td>
        <div className="job-type">
          <div className="job-type-icon">
            <Workflow size={15} />
          </div>

          {job.job_type}
        </div>
      </td>

      <td>
        <span
          className={`status-badge ${statusInfo.className}`}
        >
          <StatusIcon size={13} />

          {statusInfo.label}
        </span>
      </td>

      <td>
        {job.worker_id ? (
          <div className="worker-name">
            <span className="worker-dot" />

            {shortWorkerName(job.worker_id)}
          </div>
        ) : (
          <span className="muted">—</span>
        )}
      </td>

      <td>
        <PriorityBadge
          priority={job.priority}
        />
      </td>

      <td>{job.attempt_count}</td>

      <td>
        <div className="retry-column">
          <span>
            {job.retry_count} /{" "}
            {job.max_retries}
          </span>

          <div className="retry-track">
            <div
              className="retry-progress"
              style={{
                width: `${
                  job.max_retries
                    ? Math.min(
                        (job.retry_count /
                          job.max_retries) *
                          100,
                        100
                      )
                    : 0
                }%`,
              }}
            />
          </div>
        </div>
      </td>
    </tr>
  );
}

function PriorityBadge({ priority }) {
  let label = "Normal";
  let className = "normal";

  if (priority >= 100) {
    label = "Critical";
    className = "critical";
  } else if (priority >= 10) {
    label = "High";
    className = "high";
  } else if (priority <= 1) {
    label = "Low";
    className = "low";
  }

  return (
    <span
      className={`priority-badge ${className}`}
    >
      {label}
      <span>{priority}</span>
    </span>
  );
}

function getStatusInfo(job) {
  if (
    job.status === "scheduled" &&
    job.retry_count > 0
  ) {
    return {
      label: "Retrying",
      className: "status-retrying",
      icon: RefreshCw,
    };
  }

  switch (job.status) {
    case "queued":
      return {
        label: "Queued",
        className: "status-queued",
        icon: Clock3,
      };

    case "running":
      return {
        label: "Running",
        className: "status-running",
        icon: Activity,
      };

    case "succeeded":
      return {
        label: "Succeeded",
        className: "status-success",
        icon: CheckCircle2,
      };

    case "dead":
      return {
        label: "Dead",
        className: "status-dead",
        icon: XCircle,
      };

    case "blocked":
      return {
        label: "Blocked",
        className: "status-blocked",
        icon: Clock3,
      };

    case "scheduled":
      return {
        label: "Scheduled",
        className: "status-scheduled",
        icon: Clock3,
      };

    default:
      return {
        label: job.status,
        className: "status-default",
        icon: Clock3,
      };
  }
}

function shortWorkerName(worker) {
  if (worker.length <= 22) {
    return worker;
  }

  return `${worker.slice(0, 18)}...`;
}

export default App;