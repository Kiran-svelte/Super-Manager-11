import React, { useState, useEffect } from "react";
import { Plug, XCircle, Link as LinkIcon, RefreshCcw } from "lucide-react";
import { apiUrl } from "../lib/apiBase";
import "./IntegrationsHub.css";

export default function IntegrationsHub({ userId = "default" }) {
  const [connected, setConnected] = useState([]);
  const [available, setAvailable] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);

  const fetchIntegrations = async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl(`/api/integrations/?user_id=${encodeURIComponent(userId)}`));
      if (res.ok) {
        const data = await res.json();
        setConnected(data.connected || []);
        setAvailable(data.available || []);
      }
    } catch (err) {
      console.error("Failed to fetch integrations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntegrations();
  }, [userId]);

  const handleConnect = async (service) => {
    setProcessing(service);
    try {
      const res = await fetch(apiUrl('/api/integrations/connect'), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, service })
      });
      if (res.ok) {
        const data = await res.json();
        const redirectUrl = data.oauth_url || data.auth_url || data.authorization_url;
        if (redirectUrl) {
          // Open OAuth in new window to preserve chat state
          const oauthWindow = window.open(redirectUrl, '_blank', 'width=600,height=700');
          // Poll to check if window closed (user completed OAuth)
          const checkClosed = setInterval(() => {
            if (oauthWindow && oauthWindow.closed) {
              clearInterval(checkClosed);
              // Refresh integrations after OAuth completes
              fetchIntegrations();
            }
          }, 1000);
        } else {
          // If no auth_url, maybe it's mock connected
          await fetchIntegrations();
        }
      }
    } catch (err) {
      console.error("Connect error:", err);
    } finally {
      setProcessing(null);
    }
  };

  const handleRevoke = async (service) => {
    if (!window.confirm(`Are you sure you want to revoke access to ${service}?`)) return;
    setProcessing(service);
    try {
      const res = await fetch(apiUrl(`/api/integrations/service/${encodeURIComponent(service)}?user_id=${encodeURIComponent(userId)}`), {
        method: "DELETE",
      });
      if (res.ok) {
        await fetchIntegrations(); // Refresh list
      }
    } catch (err) {
      console.error("Revoke error:", err);
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div className="integrations-hub" style={{ 
      width: '100%', 
      padding: '16px', 
      maxHeight: 'calc(100vh - 140px)', 
      overflowY: 'auto',
      overflowX: 'hidden'
    }}>
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-white">
        <Plug className="w-5 h-5 text-blue-400" />
        Integrations Hub
      </h2>

      {loading ? (
        <div className="integration-loader">
          <RefreshCcw className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : (
        <>
          <section className="integrations-section mb-10">
            <h3 className="text-xl font-semibold mb-4 text-gray-300 border-b border-white/10 pb-2">Connected Apps</h3>
            {connected.length === 0 ? (
              <div className="empty-state">No integrations connected yet.</div>
            ) : (
              <div className="integration-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {connected.map((app) => (
                  <div key={app.service} className="integration-card bg-gray-800/80 p-4 rounded-lg border border-gray-700 hover:border-gray-600 transition flex flex-col">
                    <div className="integration-header flex items-center gap-3 mb-2">
                      <span className="text-3xl">{app.icon || "🔗"}</span>
                      <div>
                        <h4 className="font-bold text-gray-100 m-0">{app.name || app.service}</h4>
                        <span className="integration-status connected text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400">Connected</span>
                      </div>
                    </div>
                    <div className="text-sm text-gray-400 mb-4 flex-1">
                      Connected on {new Date(app.connected_at).toLocaleDateString()}
                    </div>
                    <div className="integration-actions flex justify-end">
                      <button 
                        onClick={() => handleRevoke(app.service)}
                        disabled={processing === app.service}
                        className="btn-revoke px-3 py-1.5 rounded-md bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition disabled:opacity-50 text-sm"
                      >
                        {processing === app.service ? "Revoking..." : "Revoke Access"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="integrations-section">
            <h3 className="text-xl font-semibold mb-4 text-gray-300 border-b border-white/10 pb-2">Available Integrations</h3>
            {available.length === 0 ? (
              <div className="empty-state">All available apps are connected!</div>
            ) : (
              <div className="integration-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {available.map((app) => (
                  <div key={app.service} className="integration-card bg-gray-800/50 p-4 rounded-lg border border-gray-700/50 hover:border-gray-600 transition flex flex-col">
                    <div className="integration-header flex items-center gap-3 mb-2">
                      <span className="text-3xl">{app.icon || "🔗"}</span>
                      <div>
                        <h4 className="font-bold text-gray-200 m-0">{app.name || app.service}</h4>
                        <span className="integration-status available text-xs px-2 py-0.5 rounded-full bg-gray-500/20 text-gray-400">Not Connected</span>
                      </div>
                    </div>
                    <div className="integration-desc text-sm text-gray-400 mb-4 flex-1">
                      {app.description}
                    </div>
                    <div className="integration-actions flex justify-end">
                      <button 
                        onClick={() => handleConnect(app.service)}
                        disabled={processing === app.service}
                        className="btn-connect px-3 py-1.5 rounded-md bg-blue-500 text-white font-medium hover:bg-blue-600 shadow-lg shadow-blue-500/20 transition disabled:opacity-50 flex items-center gap-1 text-sm"
                      >
                        <LinkIcon className="w-4 h-4" />
                        {processing === app.service ? "Connecting..." : "Connect"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}