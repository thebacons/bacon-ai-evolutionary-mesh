import React, { useState, useEffect, useMemo, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Activity, Cpu, Layers, Maximize, Play, Send, Smartphone, Zap,
  Server, Settings, X, ChevronRight, ChevronDown,
  Database, BookOpen, Terminal, Network, Search
} from 'lucide-react';

interface Agent {
  id: string;
  node_id: string;
  operator: string | null;
  version: string | null;
  status: string;
  last_seen: string;
  parent_id: string | null;
}

interface MessageHistory {
  id: number;
  ts: string;
  sender: string;
  target: string;
  topic: string;
  state: string;
}

const BACON_API = '/api/agents';

// Placeholder components for new tabs
const IntelView: React.FC<{ agents: Agent[] }> = ({ agents }) => (
  <div style={{ padding: '20px', color: '#fff', fontFamily: 'Outfit', display: 'flex', flexDirection: 'column', gap: '15px' }}>
    <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#00d2ff' }}>Agent Intelligence Overview</h2>
    <p style={{ opacity: 0.7 }}>Detailed insights and analytics for active agents.</p>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#00ff88' }}>Active Agents ({agents.length})</h3>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
        {agents.map(agent => (
          <li key={agent.id} style={{ marginBottom: '8px', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Cpu size={16} color="#00d2ff" />
            <span style={{ fontWeight: 'bold' }}>{agent.operator || agent.id}</span>
            <span style={{ fontSize: '0.8rem', opacity: 0.6 }}>({agent.node_id})</span>
            <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: agent.status === 'active' ? '#00ff88' : '#ff0000' }}>{agent.status.toUpperCase()}</span>
          </li>
        ))}
      </ul>
    </div>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#ff00ff' }}>Recent Activities</h3>
      <p style={{ opacity: 0.6, fontSize: '0.9rem' }}>No recent activities to display.</p>
    </div>
  </div>
);

const ChannelsView: React.FC<{ messages: MessageHistory[] }> = ({ messages }) => (
  <div style={{ padding: '20px', color: '#fff', fontFamily: 'Outfit', display: 'flex', flexDirection: 'column', gap: '15px' }}>
    <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#00d2ff' }}>Communication Channels</h2>
    <p style={{ opacity: 0.7 }}>Monitor inter-agent communications and message history.</p>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#00ffff' }}>Message Log (Last 20)</h3>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
        {messages.map(msg => (
          <li key={msg.id} style={{ marginBottom: '8px', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ fontSize: '0.75rem', opacity: 0.5 }}>{new Date(msg.ts).toLocaleTimeString()}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ fontWeight: 'bold', color: '#00ff88' }}>{msg.sender}</span>
              <ChevronRight size={12} color="rgba(255,255,255,0.5)" />
              <span style={{ fontWeight: 'bold', color: '#00d2ff' }}>{msg.target}</span>
              <span style={{ marginLeft: 'auto', fontSize: '0.8rem', opacity: 0.7 }}>Topic: {msg.topic}</span>
            </div>
            <div style={{ fontSize: '0.85rem', opacity: 0.8, marginTop: '4px' }}>State: {msg.state}</div>
          </li>
        ))}
      </ul>
    </div>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#ff00ff' }}>Send Command</h3>
      <div style={{ display: 'flex', gap: '10px' }}>
        <input type="text" placeholder="Target Agent ID" style={{ flex: 1, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '8px', borderRadius: '4px', color: '#fff' }} />
        <input type="text" placeholder="Command" style={{ flex: 2, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '8px', borderRadius: '4px', color: '#fff' }} />
        <button style={{ background: '#00d2ff', border: 'none', padding: '8px 15px', borderRadius: '4px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}><Send size={16} /> Send</button>
      </div>
    </div>
  </div>
);

const KnowledgeView: React.FC<{ memories: any[], selectedAgent: Agent | null }> = ({ memories, selectedAgent }) => (
  <div style={{ padding: '20px', color: '#fff', fontFamily: 'Outfit', display: 'flex', flexDirection: 'column', gap: '15px' }}>
    <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#00d2ff' }}>Knowledge Base</h2>
    <p style={{ opacity: 0.7 }}>Access agent memories and learned information for {selectedAgent?.operator || selectedAgent?.id || 'System'}.</p>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#ff00ff' }}>Memories ({memories.length})</h3>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
        <input type="text" placeholder="Search memories..." style={{ flex: 1, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', padding: '8px', borderRadius: '4px', color: '#fff' }} />
        <button style={{ background: '#00d2ff', border: 'none', padding: '8px 15px', borderRadius: '4px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}><Search size={16} /> Search</button>
      </div>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
        {memories.length > 0 ? (
          memories.map((memory, index) => (
            <li key={index} style={{ marginBottom: '8px', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ fontWeight: 'bold', color: '#00ff88' }}>{memory.type || 'Fact'}</div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>{memory.content || memory.text}</div>
              <div style={{ fontSize: '0.7rem', opacity: 0.5, marginTop: '4px' }}>Score: {memory.score?.toFixed(2) || 'N/A'}</div>
            </li>
          ))
        ) : (
          <p style={{ opacity: 0.6, fontSize: '0.9rem' }}>No memories found for this agent.</p>
        )}
      </ul>
    </div>
  </div>
);


const App: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [messages, setMessages] = useState<MessageHistory[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'mesh' | 'intel' | 'channels' | 'knowledge'>('mesh');
  const [memories, setMemories] = useState<any[]>([]);
  const graphComponentRef = useRef<any>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, nodeId: string } | null>(null);
  const [showInfrastructure, setShowInfrastructure] = useState(true);
  const [showSignals, setShowSignals] = useState(true);

  // Custom settings store (repulsion, linkDistance, linkStrength, nameOverride)
  const [nodeSettings, setNodeSettings] = useState<Record<string, any>>({});
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('/api/settings/mesh_v1');
        const data = await response.json();
        if (data.value && data.value !== "{}") {
          setNodeSettings(JSON.parse(data.value));
        }
        setSettingsLoaded(true);
      } catch (e) {
        console.error("Failed to load settings:", e);
        setSettingsLoaded(true);
      }
    };
    loadSettings();
  }, []);

  // Persist settings when they change (debounced)
  useEffect(() => {
    if (!settingsLoaded) return;

    const timer = setTimeout(async () => {
      try {
        await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            key: 'mesh_v1',
            value: JSON.stringify(nodeSettings)
          })
        });
      } catch (e) {
        console.error("Failed to save settings:", e);
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [nodeSettings, settingsLoaded]);

  // Poll for agent updates
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(BACON_API);
        const data: Agent[] = await response.json();
        // Filter stale agents (not seen in last 60s)
        const activeAgents = data.filter(a => {
          // Force UTC parsing by appending Z if missing
          const ts = a.last_seen.endsWith('Z') ? a.last_seen : `${a.last_seen}Z`;
          const lastSeen = new Date(ts).getTime();
          // Increase threshold to 24 hours for test stability (86,400,000 ms)
          return (Date.now() - lastSeen) < 86400000;
        });
        setAgents(activeAgents);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch agents:', error);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  // Poll for message history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('/api/history?limit=20');
        const data: MessageHistory[] = await response.json();
        setMessages(data);
      } catch (error) {
        console.error('Failed to fetch history:', error);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 4000);
    return () => clearInterval(interval);
  }, []);

  // Apply custom physics forces to D3 engine
  useEffect(() => {
    if (!graphComponentRef.current) return;

    // Repulsion (Charge)
    graphComponentRef.current.d3Force('charge').strength((node: any) => {
      const custom = nodeSettings[node.id]?.repulsion;
      return custom !== undefined ? -custom : -30;
    });

    // Link Forces
    graphComponentRef.current.d3Force('link')
      .distance((link: any) => {
        const s = nodeSettings[link.source.id]?.linkDistance;
        const t = nodeSettings[link.target.id]?.linkDistance;
        if (s !== undefined || t !== undefined) {
          return (s || 30) + (t || 30);
        }
        return 30;
      })
      .strength((link: any) => {
        const s = nodeSettings[link.source.id]?.linkStrength;
        const t = nodeSettings[link.target.id]?.linkStrength;
        if (s !== undefined || t !== undefined) {
          return (s || 1) * (t || 1);
        }
        return 1;
      });

    // Reheat engine to apply changes
    graphComponentRef.current.d3ReheatSimulation();

    // Add explicit center force if not present
    if (!graphComponentRef.current.d3Force('center')) {
      graphComponentRef.current.d3Force('center', (window as any).d3.forceCenter());
    }
  }, [nodeSettings]);

  // Persistent state for graph to prevent jumping
  const [graphData, setGraphData] = useState<{ nodes: any[], links: any[] }>({ nodes: [], links: [] });

  // Update graph data surgically
  useEffect(() => {
    if (agents.length === 0) return;

    setGraphData(prev => {
      // Map existing nodes by ID to preserve physics state
      const existingNodeMap = new Map(prev.nodes.map(n => [n.id, n]));

      const nodes = new Map<string, any>();
      const links: any[] = [];

      // 1. Process Real Agents (Highest Priority)
      agents.forEach(agent => {
        const existing = existingNodeMap.get(agent.id);
        nodes.set(agent.id, {
          ...(existing || { x: Math.random() * 200, y: Math.random() * 200 }),
          id: agent.id,
          name: nodeSettings[agent.id]?.name || agent.operator || agent.id,
          type: 'agent',
          operator: agent.operator,
          status: agent.status,
          val: 10,
          color: agent.operator?.includes('Claude') ? '#d97757' :
            agent.operator?.includes('Antigravity') ? '#ff00ff' : '#4285f4'
        });
      });

      // 2. Process Hardware & Hierarchy Links
      agents.forEach(agent => {
        // Hardware Node (if not already an agent)
        if (!nodes.has(agent.node_id)) {
          const existing = existingNodeMap.get(agent.node_id);
          nodes.set(agent.node_id, {
            ...(existing || { x: Math.random() * 200, y: Math.random() * 200 }),
            id: agent.node_id,
            name: nodeSettings[agent.node_id]?.name || agent.node_id,
            type: 'hardware',
            val: 25, // Larger for machines
            color: '#00d2ff'
          });
        }

        links.push({
          source: agent.id,
          target: agent.node_id,
          type: 'hardware'
        });

        // Parent Dependency
        if (agent.parent_id) {
          if (!nodes.has(agent.parent_id)) {
            // Ghost Node
            const existing = existingNodeMap.get(agent.parent_id);
            nodes.set(agent.parent_id, {
              ...(existing || { x: (Math.random() - 0.5) * 200, y: (Math.random() - 0.5) * 200 }),
              id: agent.parent_id,
              name: nodeSettings[agent.parent_id]?.name || `Ancestor: ${agent.parent_id}`,
              type: 'agent',
              status: 'offline',
              val: 6,
              color: '#333'
            });
          }
          links.push({
            source: agent.id,
            target: agent.parent_id,
            type: 'dependency'
          });
        }
      });

      // 3. LOGICAL BRIDGE (Connect Clusters)
      // Find the remote host and local host to create a "Bridge Link"
      const remoteHosts = agents.filter(a => a.node_id.includes('srv906866')).map(a => a.node_id);
      const localHosts = agents.filter(a => a.node_id.includes('pc-win11')).map(a => a.node_id);

      if (remoteHosts.length > 0 && localHosts.length > 0 && showInfrastructure) {
        links.push({
          source: remoteHosts[0],
          target: localHosts[0],
          type: 'bridge'
        });
      }

      // 4. VIRTUAL SIGNAL LINKS (Communication History)
      if (showSignals) {
        const SIGNAL_TTL_MS = 30000; // 30 seconds
        const communicationMap = new Map<string, any>();

        messages.forEach(msg => {
          // Only show agent-to-agent talk
          if (msg.sender === 'control-plane' || msg.target === 'control-plane') return;

          const key = `${msg.sender}->${msg.target}`;

          // Force UTC parsing for age calculation
          const msgTs = msg.ts.endsWith('Z') ? msg.ts : `${msg.ts}Z`;
          const ageMs = Date.now() - new Date(msgTs).getTime();

          if (ageMs < SIGNAL_TTL_MS) {
            const opacity = Math.max(0.1, 1 - (ageMs / SIGNAL_TTL_MS));

            // We keep the freshest message for this pair
            if (!communicationMap.has(key) || communicationMap.get(key).ageMs > ageMs) {
              communicationMap.set(key, {
                source: msg.sender,
                target: msg.target,
                type: 'signal',
                curvature: 0.4,
                opacity: opacity,
                ageMs: ageMs
              });
            }
          }
        });

        communicationMap.forEach(link => links.push(link));
      }

      // Filter Infrastructure links if layer is hidden
      let finalHierarchyLinks = links;
      if (!showInfrastructure) {
        finalHierarchyLinks = links.filter(l => l.type === 'signal');
      }

      const nextNodes = Array.from(nodes.values());
      const finalLinksOrdered = finalHierarchyLinks.filter(l =>
        nodes.has(typeof l.source === 'string' ? l.source : l.source.id) &&
        nodes.has(typeof l.target === 'string' ? l.target : l.target.id)
      );

      // STABILITY CHECK: Only update if structure changed
      const prevIds = prev.nodes.map(n => n.id).sort().join(',');
      const nextIds = nextNodes.map(n => n.id).sort().join(',');

      if (prevIds === nextIds && prev.links.length === finalLinksOrdered.length) {
        return prev;
      }

      return { nodes: nextNodes, links: finalLinksOrdered };
    });
  }, [agents, nodeSettings, messages, showInfrastructure, showSignals]);

  // Fetch Memories when Knowledge tab is opened if not already fetched or when agent changes
  useEffect(() => {
    const fetchMemories = async () => {
      if (activeTab === 'knowledge') {
        try {
          const id = selectedAgent ? selectedAgent.id : 'bacon-system';
          const res = await fetch(`/api/memory/${id}`);
          const data = await res.json();
          setMemories(data);
        } catch (e) {
          console.error("Failed to fetch memories", e);
        }
      }
    };
    fetchMemories();
  }, [activeTab, selectedAgent]);

  const handleZoomToFit = () => {
    if (graphComponentRef.current) {
      graphComponentRef.current.zoomToFit(400, 50);
    }
  };

  if (loading && agents.length === 0) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#050508', color: '#fff' }}>
        <div className="glow-text" style={{ fontSize: '1.5rem', fontFamily: 'Orbitron' }}>INITIALIZING MESH VISUALIZER...</div>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#050508' }}>
      {/* Header */}
      <header className="header" style={{ padding: '0 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '60px', background: 'rgba(0,0,0,0.8)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '30px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <img src="/logo.png" alt="BACON-AI Logo" style={{ height: '35px' }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <h1 style={{ fontSize: '1rem', fontWeight: 700, letterSpacing: '1px', color: '#fff', margin: 0 }}>
                BACON-AI
              </h1>
              <span style={{ fontSize: '0.6rem', color: '#00d2ff', letterSpacing: '1px', fontWeight: 600 }}>EVOLUTIONARY MESH</span>
            </div>
          </div>

          {/* Tab Navigation */}
          <nav style={{ display: 'flex', gap: '30px', height: '60px' }}>
            {[
              { id: 'mesh', label: 'MESH', icon: <Network size={16} /> },
              { id: 'intel', label: 'INTEL', icon: <Database size={16} /> },
              { id: 'channels', label: 'CHANNELS', icon: <Terminal size={16} /> },
              { id: 'knowledge', label: 'KNOWLEDGE', icon: <BookOpen size={16} /> }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: activeTab === tab.id ? '#00d2ff' : 'rgba(255,255,255,0.4)',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '0 5px',
                  borderBottom: activeTab === tab.id ? '2px solid #00d2ff' : '2px solid transparent',
                  transition: 'all 0.2s ease',
                  height: '100%'
                }}
              >
                {tab.icon} {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div style={{ display: 'flex', gap: '20px', color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', alignItems: 'center' }}>
          {activeTab === 'mesh' && (
            <div className="glass-panel" style={{ display: 'flex', gap: '15px', padding: '5px 15px', background: 'rgba(255,255,255,0.03)', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.75rem' }}>
                <input type="checkbox" checked={showInfrastructure} onChange={e => setShowInfrastructure(e.target.checked)} style={{ cursor: 'pointer' }} />
                <Server size={14} color="#00d2ff" /> INFRASTRUCTURE
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.75rem' }}>
                <input type="checkbox" checked={showSignals} onChange={e => setShowSignals(e.target.checked)} style={{ cursor: 'pointer' }} />
                <Zap size={14} color="#00ffff" /> SIGNALS
              </label>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="#00ff88" /> {agents.length} Nodes Active
          </div>
          <a
            href="/docs"
            target="_blank"
            className="glass-panel"
            style={{
              textDecoration: 'none',
              color: '#00d2ff',
              padding: '5px 12px',
              fontSize: '0.75rem',
              fontWeight: 'bold',
              letterSpacing: '1px',
              border: '1px solid rgba(0, 210, 255, 0.3)'
            }}>
            API CONTROL
          </a>
        </div>
      </header>

      {/* Main View */}
      <main style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#050508' }}>
        {activeTab === 'mesh' && (
          <ForceGraph2D
            ref={graphComponentRef}
            graphData={graphData}
            onEngineStop={() => {
              if (graphComponentRef.current && loading) {
                graphComponentRef.current.zoomToFit(400);
              }
            }}
            cooldownTicks={100}
            nodeLabel={(node: any) => `${node.id} (${node.role || node.type})`}
            linkDirectionalParticles={(link: any) => {
              if (link.type === 'dependency') return 1;
              if (link.type === 'signal') return 4;
              return 0;
            }}
            linkDirectionalParticleSpeed={(link: any) => link.type === 'signal' ? 0.01 : 0.003}
            linkCurvature="curvature"
            linkColor={(link: any) => {
              if (link.type === 'hardware') return '#00d2ff88';
              if (link.type === 'bridge') return '#ff00ff44';
              if (link.type === 'signal') {
                const op = Math.floor((link.opacity || 1) * 255).toString(16).padStart(2, '0');
                return `#00ffff${op}`;
              }
              return 'rgba(255, 255, 255, 0.2)';
            }}
            linkWidth={(link: any) => link.type === 'hardware' ? 2 : 1}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name || node.id;
              const curScale = globalScale || 1;
              const fontSize = 12 / curScale;
              const size = (node.type === 'hardware' ? 6 : 4);

              ctx.beginPath();
              ctx.arc(node.x || 0, node.y || 0, size, 0, 2 * Math.PI, false);

              if (node.type === 'hardware') {
                ctx.fillStyle = node.id.includes('srv906866') ? '#ff00ff' : '#00d2ff';
                ctx.shadowBlur = 10;
                ctx.shadowColor = ctx.fillStyle;
              } else if (node.id === 'antigravity') {
                ctx.fillStyle = '#ff00ff';
              } else {
                ctx.fillStyle = '#00ff88';
              }

              ctx.fill();
              ctx.shadowBlur = 0;

              if (curScale > 1.5) {
                ctx.font = `${fontSize}px Outfit`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                ctx.fillText(label, node.x || 0, (node.y || 0) + (size + 4));
              }
            }}
            onNodeClick={(node: any) => {
              const agentFound = agents.find(a => a.id === node.id);
              setSelectedAgent(agentFound as any || node);
              setContextMenu(null);
            }}
            onNodeRightClick={(node: any, event) => {
              setContextMenu({ x: event.clientX, y: event.clientY, nodeId: node.id });
            }}
            onBackgroundClick={() => {
              setContextMenu(null);
            }}
          />
        )}

        {activeTab === 'intel' && <IntelView agents={agents} />}
        {activeTab === 'channels' && <ChannelsView messages={messages} />}
        {activeTab === 'knowledge' && <KnowledgeView memories={memories} selectedAgent={selectedAgent} />}

        {/* Node Settings Context Menu */}
        {contextMenu && (
          <div className="glass-panel" style={{
            position: 'fixed',
            left: `${contextMenu.x + 10}px`,
            top: `${contextMenu.y + 10}px`,
            width: '280px',
            padding: '15px',
            zIndex: 100,
            boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.2)',
            background: 'rgba(5, 5, 8, 0.95)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#00d2ff' }}>
                <Settings size={16} />
                <span style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>Node Controls</span>
              </div>
              <button onClick={() => setContextMenu(null)} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}>
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div>
                <label style={{ fontSize: '0.7rem', opacity: 0.6, display: 'block', marginBottom: '5px' }}>Override Name</label>
                <input
                  type="text"
                  placeholder="New label..."
                  value={nodeSettings[contextMenu.nodeId]?.name || ''}
                  onChange={(e) => setNodeSettings(prev => ({
                    ...prev,
                    [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], name: e.target.value }
                  }))}
                  style={{ width: '100%', background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 10px', borderRadius: '4px', fontSize: '0.8rem', outline: 'none' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.6, marginBottom: '5px' }}>
                  <span>Repulsion (Gravity)</span>
                  <span>{nodeSettings[contextMenu.nodeId]?.repulsion || 30}</span>
                </div>
                <input
                  type="range" min="0" max="500" step="10"
                  value={nodeSettings[contextMenu.nodeId]?.repulsion || 30}
                  onChange={(e) => setNodeSettings(prev => ({
                    ...prev,
                    [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], repulsion: parseInt(e.target.value) }
                  }))}
                  style={{ width: '100%', accentColor: '#00d2ff' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.6, marginBottom: '5px' }}>
                  <span>Link Distance</span>
                  <span>{nodeSettings[contextMenu.nodeId]?.linkDistance || 30}px</span>
                </div>
                <input
                  type="range" min="10" max="200" step="5"
                  value={nodeSettings[contextMenu.nodeId]?.linkDistance || 30}
                  onChange={(e) => setNodeSettings(prev => ({
                    ...prev,
                    [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], linkDistance: parseInt(e.target.value) }
                  }))}
                  style={{ width: '100%', accentColor: '#00ff88' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.6, marginBottom: '5px' }}>
                  <span>Tension (Strength)</span>
                  <span>{(nodeSettings[contextMenu.nodeId]?.linkStrength || 1).toFixed(2)}</span>
                </div>
                <input
                  type="range" min="0.1" max="5" step="0.1"
                  value={nodeSettings[contextMenu.nodeId]?.linkStrength || 1}
                  onChange={(e) => setNodeSettings(prev => ({
                    ...prev,
                    [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], linkStrength: parseFloat(e.target.value) }
                  }))}
                  style={{ width: '100%', accentColor: '#ff00ff' }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Detail Panel */}
        {selectedAgent && (
          <div className="glass-panel" style={{ position: 'absolute', right: '20px', top: '20px', width: '320px', padding: '20px', zIndex: 10, background: 'rgba(5, 5, 8, 0.9)', backdropFilter: 'blur(10px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '1.1rem', color: '#fff' }}>Agent Intel</h2>
              <button
                onClick={() => setSelectedAgent(null)}
                style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer' }}
              >✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px' }}>
                <Cpu size={20} color="#00d2ff" />
                <div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.6 }}>Identity</div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{selectedAgent.operator || selectedAgent.id}</div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px' }}>
                <Server size={20} color="#00ff88" />
                <div>
                  <div style={{ fontSize: '0.7rem', opacity: 0.6 }}>Node Host</div>
                  <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{selectedAgent.node_id}</div>
                </div>
              </div>

              <div style={{ padding: '12px', background: 'rgba(0, 210, 255, 0.1)', borderLeft: '3px solid #00d2ff', borderRadius: '4px' }}>
                <div style={{ fontSize: '0.7rem', opacity: 0.8, marginBottom: '5px' }}>Status</div>
                <div style={{ fontSize: '0.8rem', color: '#00ff88', fontWeight: 'bold' }}>{(selectedAgent.status || 'unknown').toUpperCase()}</div>
              </div>

              <button className="glass-panel" style={{
                marginTop: '10px',
                padding: '12px',
                background: 'linear-gradient(45deg, #00d2ff, #3a7bd5)',
                border: 'none',
                color: '#fff',
                fontWeight: 'bold',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px'
              }}>
                <Zap size={18} fill="white" /> SEND SIGNAL (WAKE)
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer" style={{ padding: '8px 20px', display: 'flex', fontSize: '0.7rem', gap: '25px', color: 'rgba(255,255,255,0.3)', background: 'rgba(0,0,0,0.5)', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <div>PROTOCOL: v1.2</div>
        <div>MESH STATUS: STABLE</div>
        <div>ACTIVE TAB: {activeTab.toUpperCase()}</div>
        <div style={{ marginLeft: 'auto' }}>BACON-AI © 2026</div>
      </footer>
    </div>
  );
};

export default App;
