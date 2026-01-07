import React, { useState, useEffect, useMemo, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceX, forceY } from 'd3';
import {
  Activity, Cpu, Layers, Maximize, Play, Send, Smartphone, Zap,
  Server, Settings, X, ChevronRight, ChevronDown,
  Database, BookOpen, Terminal, Network, Search
} from 'lucide-react';

// Robust polyfill for crypto.randomUUID in non-secure (HTTP) contexts
if (typeof window !== 'undefined' && (!window.crypto || !window.crypto.randomUUID)) {
  if (!window.crypto) (window as any).crypto = {};
  (window.crypto as any).randomUUID = function () {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  };
}

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

// Helper Component for Legend
const LegendItem = ({ color, label, shape, isLink, onClick }: {
  color: string,
  label: string,
  shape?: string,
  isLink?: boolean,
  onClick?: () => void
}) => (
  <div
    onClick={onClick}
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '0.75rem',
      cursor: onClick ? 'pointer' : 'default',
      transition: 'opacity 0.2s',
      background: 'rgba(255,255,255,0.03)',
      padding: '6px 10px',
      borderRadius: '6px'
    }}
  >
    <div style={{
      width: isLink ? '20px' : '12px',
      height: isLink ? '2px' : '12px',
      background: color,
      borderRadius: shape === 'circle' ? '50%' : (shape === 'square' ? '2px' : '0'),
      clipPath: shape === 'triangle' ? 'polygon(50% 0%, 0% 100%, 100% 100%)' :
        shape === 'diamond' ? 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' :
          shape === 'hexagon' ? 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)' : 'none',
      boxShadow: `0 0 8px ${color}`
    }} />
    <span style={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600, flex: 1 }}>{label}</span>
    {onClick && <Settings size={12} color="rgba(255,255,255,0.4)" />}
  </div>
);

// Network Legend Panel
const Legend: React.FC<{ typeConfigs: any, setCustomizingType: (t: string | null) => void }> = ({ typeConfigs, setCustomizingType }) => (
  <div className="glass-panel" style={{
    position: 'absolute',
    top: '20px',
    left: '20px',
    padding: '20px',
    background: 'rgba(5,5,10,0.85)',
    backdropFilter: 'blur(15px)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '16px',
    zIndex: 10,
    width: '260px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.4)'
  }}>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '0.7rem',
      color: '#ff00ff',
      fontWeight: 'bold',
      letterSpacing: '2px',
      marginBottom: '15px',
      textTransform: 'uppercase'
    }}>
      <Network size={14} /> Mesh Identities
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <LegendItem
        color={typeConfigs.hub.color}
        label={typeConfigs.hub.label}
        shape={typeConfigs.hub.shape}
        onClick={() => setCustomizingType('hub')}
      />
      <LegendItem
        color={typeConfigs.infrastructure.color}
        label={typeConfigs.infrastructure.label}
        shape={typeConfigs.infrastructure.shape}
        onClick={() => setCustomizingType('infrastructure')}
      />
      <LegendItem
        color={typeConfigs.mainAgent.color}
        label={typeConfigs.mainAgent.label}
        shape={typeConfigs.mainAgent.shape}
        onClick={() => setCustomizingType('mainAgent')}
      />
      <LegendItem
        color={typeConfigs.subAgent.color}
        label={typeConfigs.subAgent.label}
        shape={typeConfigs.subAgent.shape}
        onClick={() => setCustomizingType('subAgent')}
      />
      <LegendItem color="#00ffff" label="Evolutionary Signal" isLink />
    </div>
    <div style={{ marginTop: '15px', fontSize: '0.65rem', opacity: 0.5, fontStyle: 'italic', textAlign: 'center' }}>
      Click an item to customize visual style
    </div>
  </div>
);

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
  </div>
);

const KnowledgeView: React.FC<{ memories: any[], selectedAgent: Agent | null }> = ({ memories, selectedAgent }) => (
  <div style={{ padding: '20px', color: '#fff', fontFamily: 'Outfit', display: 'flex', flexDirection: 'column', gap: '15px' }}>
    <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#00d2ff' }}>Knowledge Base</h2>
    <p style={{ opacity: 0.7 }}>Access agent memories and learned information for {selectedAgent?.operator || selectedAgent?.id || 'System'}.</p>
    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1.1rem', color: '#ff00ff' }}>Memories ({memories.length})</h3>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0, maxHeight: 'calc(100vh - 300px)', overflowY: 'auto' }}>
        {memories.length > 0 ? (
          memories.map((memory, index) => (
            <li key={index} style={{ marginBottom: '8px', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ fontWeight: 'bold', color: '#00ff88' }}>{memory.type || 'Fact'}</div>
              <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>{memory.content || memory.text}</div>
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
  const firstZoomDone = useRef(false);
  const [contextMenu, setContextMenu] = useState<{ x: number, y: number, nodeId: string } | null>(null);
  const [showInfrastructure, setShowInfrastructure] = useState(true);
  const [showSignals, setShowSignals] = useState(true);

  // Custom settings store (repulsion, linkDistance, linkStrength, nameOverride)
  const [nodeSettings, setNodeSettings] = useState<Record<string, any>>({});
  const [typeConfigs, setTypeConfigs] = useState<Record<string, any>>({
    hub: { shape: 'circle', color: '#ff00ff', label: 'Hostinger Hub', baseSize: 7 },
    infrastructure: { shape: 'circle', color: '#00d2ff', label: 'Local Infra', baseSize: 7 },
    mainAgent: { shape: 'triangle', color: '#d97757', label: 'Main LLM Agent', baseSize: 5 },
    subAgent: { shape: 'square', color: '#00ff88', label: 'Sub-Agent', baseSize: 4 },
  });
  const [settingsLoaded, setSettingsLoaded] = useState(false);
  const [customizingType, setCustomizingType] = useState<string | null>(null);

  // Load settings on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const response = await fetch('/api/settings/mesh_v1');
        const data = await response.json();
        if (data.value && data.value !== "{}") {
          const parsed = JSON.parse(data.value);
          if (parsed.nodeSettings) setNodeSettings(parsed.nodeSettings);
          if (parsed.typeConfigs) setTypeConfigs(prev => ({ ...prev, ...parsed.typeConfigs }));
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
    const saveSettings = async () => {
      try {
        await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            key: 'mesh_v1',
            value: JSON.stringify({ nodeSettings, typeConfigs })
          })
        });
      } catch (e) {
        console.error("Failed to save settings:", e);
      }
    };
    const timer = setTimeout(saveSettings, 1000);
    return () => clearTimeout(timer);
  }, [nodeSettings, typeConfigs, settingsLoaded]);

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
        // Do not set loading false here, wait for first zoom in onEngineStop
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

    // Repulsion (Charge) - restored to original working value
    graphComponentRef.current.d3Force('charge').strength((node: any) => {
      const custom = nodeSettings[node.id]?.repulsion;
      return custom !== undefined ? -custom : -30;
    });

    // Link Forces - Proportional distances to clearly separate clusters
    graphComponentRef.current.d3Force('link')
      .distance((link: any) => {
        const sId = typeof link.source === 'object' ? link.source.id : link.source;
        const tId = typeof link.target === 'object' ? link.target.id : link.target;

        const s = nodeSettings[sId]?.linkDistance;
        const t = nodeSettings[tId]?.linkDistance;

        if (s !== undefined || t !== undefined) {
          return (s || 30) + (t || 30);
        }

        if (link.type === 'hardware') return 30;
        if (link.type === 'dependency') return 40;
        if (link.type === 'bridge') return 100;
        return 30;
      })
      .strength((link: any) => {
        const sId = typeof link.source === 'object' ? link.source.id : link.source;
        const tId = typeof link.target === 'object' ? link.target.id : link.target;

        const s = nodeSettings[sId]?.linkStrength;
        const t = nodeSettings[tId]?.linkStrength;
        if (s !== undefined || t !== undefined) {
          return (s || 1) * (t || 1);
        }
        return link.type === 'bridge' ? 0.3 : 1;
      });

    // Gravitational Attraction
    graphComponentRef.current.d3Force('x', forceX(0).strength((node: any) => {
      return node.type === 'hardware' ? 0.05 : 0.02;
    }));

    graphComponentRef.current.d3Force('y', forceY(0).strength((node: any) => {
      return node.type === 'hardware' ? 0.05 : 0.02;
    }));

    // Wake up the simulation
    const fg = graphComponentRef.current;
    if (fg) {
      if (typeof fg.d3Simulation === 'function') {
        const sim = fg.d3Simulation();
        if (sim) {
          sim.alpha(0.3).restart();
        }
      } else if (typeof fg.d3AlphaTarget === 'function') {
        fg.d3AlphaTarget(0.3);
        setTimeout(() => {
          if (graphComponentRef.current && typeof graphComponentRef.current.d3AlphaTarget === 'function') {
            graphComponentRef.current.d3AlphaTarget(0);
          }
        }, 500);
      }
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
        const isMain = agent.operator?.includes('Claude') || agent.operator?.includes('Antigravity') || !agent.parent_id;

        nodes.set(agent.id, {
          ...(existing || { x: (Math.random() - 0.5) * 400, y: (Math.random() - 0.5) * 400 }),
          id: agent.id,
          name: nodeSettings[agent.id]?.name || agent.operator || agent.id,
          type: 'agent',
          group: isMain ? 'mainAgent' : 'subAgent',
          operator: agent.operator,
          status: agent.status,
          val: isMain ? 10 : 6
        });
      });

      // 2. Process Hardware & Hierarchy Links
      agents.forEach(agent => {
        // Hardware Node (if not already an agent)
        if (!nodes.has(agent.node_id)) {
          const existing = existingNodeMap.get(agent.node_id);
          const isHub = agent.node_id.includes('srv906866');
          nodes.set(agent.node_id, {
            ...(existing || { x: (Math.random() - 0.5) * 400, y: (Math.random() - 0.5) * 400 }),
            id: agent.node_id,
            name: nodeSettings[agent.node_id]?.name || agent.node_id,
            type: 'hardware',
            group: isHub ? 'hub' : 'infrastructure',
            val: 20
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

      // 3. NETWORK BACKBONE (Connect all hardware nodes to form a spine)
      const remoteCloud = Array.from(nodes.values()).find(n => n.type === 'hardware' && n.id.includes('srv906866'))?.id;
      const localPC = Array.from(nodes.values()).find(n => n.type === 'hardware' && n.id.includes('pc-win11'))?.id;

      const hardwareNodes = Array.from(nodes.values()).filter(n => n.type === 'hardware');

      hardwareNodes.forEach(hw => {
        // Essential: Connect Local PC to Remote Cloud (The WAN Bridge)
        if (hw.id === localPC && remoteCloud) {
          links.push({ source: hw.id, target: remoteCloud, type: 'bridge' });
        }

        // Connect other hardware to the local spine if they are likely local
        if (hw.id !== localPC && hw.id !== remoteCloud) {
          const targetNode = hw.id.includes('.cloud') || hw.id.includes('srv') ? remoteCloud : localPC;
          if (targetNode && targetNode !== hw.id) {
            links.push({ source: hw.id, target: targetNode, type: 'bridge' });
          }
        }
      });

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

      const nextNodes = Array.from(nodes.values());
      const finalLinksOrdered = links.filter(l =>
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
          <>
            <ForceGraph2D
              ref={graphComponentRef}
              graphData={graphData}
              onEngineStop={() => {
                if (graphComponentRef.current && !firstZoomDone.current && graphData.nodes.length > 0) {
                  graphComponentRef.current.zoomToFit(800, 100);
                  firstZoomDone.current = true;
                  setLoading(false);
                }
              }}
              cooldownTicks={100}
              nodeLabel={(node: any) => `${node.id} (${node.role || node.type})`}
              linkDirectionalParticles={(link: any) => {
                if (link.type === 'dependency' && showInfrastructure) return 1;
                if (link.type === 'signal' && showSignals) return 4;
                return 0;
              }}
              linkDirectionalParticleSpeed={(link: any) => link.type === 'signal' ? 0.01 : 0.003}
              linkCurvature="curvature"
              linkColor={(link: any) => {
                if (link.type === 'hardware') return showInfrastructure ? '#00d2ff88' : 'transparent';
                if (link.type === 'bridge') return showInfrastructure ? '#ff00ff22' : 'transparent'; // Faint bridge links as requested
                if (link.type === 'dependency') return showInfrastructure ? 'rgba(255, 255, 255, 0.2)' : 'transparent';
                if (link.type === 'signal') {
                  if (!showSignals) return 'transparent';
                  const op = Math.floor((link.opacity || 1) * 255).toString(16).padStart(2, '0');
                  return `#00ffff${op}`;
                }
                return 'transparent';
              }}
              linkWidth={(link: any) => link.type === 'hardware' ? 2 : 1}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                // If it's a hardware node and we're hiding infrastructure, don't draw it
                if (node.type === 'hardware' && !showInfrastructure) return;

                // Get Visual Config for Group
                const config = typeConfigs[node.group] || { shape: 'circle', color: '#00ff88', baseSize: 4 };
                const color = config.color;
                const shape = config.shape;

                // Effective size: base size * node setting multiplier (default 1)
                const sizeMult = nodeSettings[node.id]?.sizeMultiplier || 1;
                const typeSizeMult = config.sizeMultiplier || 1;
                const size = (config.baseSize || 4) * sizeMult * typeSizeMult;

                ctx.save();
                ctx.translate(node.x, node.y);
                ctx.beginPath();

                if (shape === 'hexagon') {
                  const sides = 6;
                  ctx.moveTo(size * Math.cos(0), size * Math.sin(0));
                  for (let i = 1; i <= sides; i++) {
                    ctx.lineTo(size * Math.cos(i * 2 * Math.PI / sides), size * Math.sin(i * 2 * Math.PI / sides));
                  }
                } else if (shape === 'diamond') {
                  ctx.moveTo(0, -size * 1.3);
                  ctx.lineTo(size * 1.3, 0);
                  ctx.lineTo(0, size * 1.3);
                  ctx.lineTo(-size * 1.3, 0);
                } else if (shape === 'triangle') {
                  ctx.moveTo(0, -size * 1.3);
                  ctx.lineTo(size * 1.25, size * 0.8);
                  ctx.lineTo(-size * 1.25, size * 0.8);
                } else if (shape === 'square') {
                  ctx.rect(-size, -size, size * 2, size * 2);
                } else {
                  // Circle
                  ctx.arc(0, 0, size, 0, 2 * Math.PI, false);
                }

                ctx.closePath();
                ctx.fillStyle = color;

                if (node.type === 'hardware' || node.group === 'mainAgent') {
                  ctx.shadowBlur = 15;
                  ctx.shadowColor = color;
                }

                ctx.fill();
                ctx.restore();

                // Draw Text
                const label = node.name || node.id;
                const curScale = globalScale || 1;
                const fontSize = 14 / curScale;

                // Draw Text
                if (curScale > 0.6) {
                  ctx.font = `600 ${fontSize}px Outfit`;
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                  ctx.shadowBlur = 3;
                  ctx.shadowColor = 'black';
                  ctx.fillText(label, node.x, node.y + (size + 8));
                  ctx.shadowBlur = 0;
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

            {/* Floating Zoom Button */}
            <button
              onClick={handleZoomToFit}
              className="glass-panel"
              style={{
                position: 'absolute',
                bottom: '20px',
                right: '250px', // Move to the right side to avoid overlapping with stats/legend
                padding: '10px 15px',
                background: 'rgba(0, 210, 255, 0.15)',
                border: '1px solid rgba(0, 210, 255, 0.4)',
                color: '#00d2ff',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontWeight: 'bold',
                fontSize: '0.8rem',
                borderRadius: '4px',
                zIndex: 5
              }}
            >
              <Maximize size={16} /> ZOOM TO FIT
            </button>

            <Legend typeConfigs={typeConfigs} setCustomizingType={setCustomizingType} />

            {/* Config Popup */}
            {customizingType && (
              <div className="glass-panel" style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                padding: '25px',
                background: 'rgba(5,5,10,0.95)',
                backdropFilter: 'blur(30px)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '20px',
                zIndex: 100,
                width: '320px',
                boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                  <h3 style={{ margin: 0, fontSize: '1rem', color: '#ff00ff' }}>Customize {typeConfigs[customizingType].label}</h3>
                  <button onClick={() => setCustomizingType(null)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}>×</button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.6, marginBottom: '8px', textTransform: 'uppercase' }}>Shape</div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {['circle', 'triangle', 'square', 'hexagon', 'diamond'].map(s => (
                        <button
                          key={s}
                          onClick={() => setTypeConfigs(prev => ({ ...prev, [customizingType]: { ...prev[customizingType], shape: s } }))}
                          style={{
                            flex: 1,
                            padding: '10px 5px',
                            background: typeConfigs[customizingType].shape === s ? 'rgba(255,0,255,0.2)' : 'rgba(255,255,255,0.05)',
                            border: `1px solid ${typeConfigs[customizingType].shape === s ? '#ff00ff' : 'rgba(255,255,255,0.1)'}`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center'
                          }}
                        >
                          <div style={{
                            width: '12px',
                            height: '12px',
                            background: typeConfigs[customizingType].color,
                            borderRadius: s === 'circle' ? '50%' : (s === 'square' ? '2px' : '0'),
                            clipPath: s === 'triangle' ? 'polygon(50% 0%, 0% 100%, 100% 100%)' :
                              s === 'diamond' ? 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' :
                                s === 'hexagon' ? 'polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%)' : 'none'
                          }} />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.6, marginBottom: '8px', textTransform: 'uppercase' }}>
                      <span>Shape Size</span>
                      <span>{typeConfigs[customizingType].sizeMultiplier || 1}x</span>
                    </div>
                    <input
                      type="range" min="0.5" max="3" step="0.1"
                      value={typeConfigs[customizingType].sizeMultiplier || 1}
                      onChange={(e) => setTypeConfigs(prev => ({
                        ...prev,
                        [customizingType]: { ...prev[customizingType], sizeMultiplier: parseFloat(e.target.value) }
                      }))}
                      style={{ width: '100%', accentColor: '#ff00ff' }}
                    />
                  </div>

                  <div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.6, marginBottom: '8px', textTransform: 'uppercase' }}>Color</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
                      {['#ff00ff', '#00d2ff', '#d97757', '#00ff88', '#4285f4', '#fbbc05', '#ea4335', '#ffffff', '#7b1fa2', '#2e7d32'].map(c => (
                        <div
                          key={c}
                          onClick={() => setTypeConfigs(prev => ({ ...prev, [customizingType]: { ...prev[customizingType], color: c } }))}
                          style={{
                            width: '100%',
                            paddingTop: '100%',
                            background: c,
                            borderRadius: '50%',
                            cursor: 'pointer',
                            border: `2px solid ${typeConfigs[customizingType].color === c ? '#fff' : 'transparent'}`,
                            boxShadow: `0 0 10px ${c}44`
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => setCustomizingType(null)}
                  style={{
                    width: '100%',
                    marginTop: '25px',
                    padding: '12px',
                    background: '#ff00ff',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#fff',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                  }}
                >
                  SAVE CHANGES
                </button>
              </div>
            )}

            {/* Network Stats - Bottom Left */}
            <div className="glass-panel" style={{
              position: 'absolute',
              bottom: '20px',
              left: '20px',
              padding: '15px 20px',
              background: 'rgba(0,0,0,0.6)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              pointerEvents: 'none',
              zIndex: 10,
              width: '200px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.7rem', color: '#ff00ff', fontWeight: 'bold', letterSpacing: '2px', marginBottom: '10px' }}>
                <Activity size={14} /> NETWORK STATS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.6 }}>Nodes:</span>
                  <span style={{ color: '#00ff88', fontWeight: 'bold' }}>{agents.length}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.6 }}>Signals/sec:</span>
                  <span style={{ color: '#00d2ff', fontWeight: 'bold' }}>{(messages.length / 4).toFixed(1)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ opacity: 0.6 }}>Active Links:</span>
                  <span style={{ color: '#ff00ff', fontWeight: 'bold' }}>{graphData.links.length}</span>
                </div>
              </div>
            </div>
          </>
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

              {/* Enhanced Physics Controls with intuitive names */}
              <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '10px' }}>
                <div style={{ fontSize: '0.65rem', color: '#00d2ff', marginBottom: '10px', fontWeight: 600 }}>MESH PHYSICS CONTROLS</div>

                <div style={{ marginBottom: '15px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.8, marginBottom: '2px' }}>
                    <span>Push (Repulsion)</span>
                    <span>{nodeSettings[contextMenu.nodeId]?.repulsion || 150}</span>
                  </div>
                  <div style={{ fontSize: '0.6rem', opacity: 0.4, marginBottom: '5px' }}>Forces other nodes away from this center.</div>
                  <input
                    type="range" min="0" max="600" step="10"
                    value={nodeSettings[contextMenu.nodeId]?.repulsion || 150}
                    onPointerDown={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0.5);
                    }}
                    onPointerUp={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0);
                    }}
                    onChange={(e) => setNodeSettings(prev => ({
                      ...prev,
                      [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], repulsion: parseInt(e.target.value) }
                    }))}
                    style={{ width: '100%', accentColor: '#00d2ff' }}
                  />
                </div>

                <div style={{ marginBottom: '15px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.8, marginBottom: '2px' }}>
                    <span>Reach (Distance)</span>
                    <span>{nodeSettings[contextMenu.nodeId]?.linkDistance || 60}px</span>
                  </div>
                  <div style={{ fontSize: '0.6rem', opacity: 0.4, marginBottom: '5px' }}>The target length of its network connections.</div>
                  <input
                    type="range" min="10" max="400" step="5"
                    value={nodeSettings[contextMenu.nodeId]?.linkDistance || 60}
                    onPointerDown={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0.5);
                    }}
                    onPointerUp={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0);
                    }}
                    onChange={(e) => setNodeSettings(prev => ({
                      ...prev,
                      [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], linkDistance: parseInt(e.target.value) }
                    }))}
                    style={{ width: '100%', accentColor: '#00ff88' }}
                  />
                </div>

                <div style={{ marginBottom: '15px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.8, marginBottom: '2px' }}>
                    <span>Stiffness (Tension)</span>
                    <span>{(nodeSettings[contextMenu.nodeId]?.linkStrength || 1).toFixed(2)}x</span>
                  </div>
                  <div style={{ fontSize: '0.6rem', opacity: 0.4, marginBottom: '5px' }}>How strictly Reach is enforced vs Push.</div>
                  <input
                    type="range" min="0.05" max="3" step="0.05"
                    value={nodeSettings[contextMenu.nodeId]?.linkStrength || 1}
                    onPointerDown={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0.5);
                    }}
                    onPointerUp={() => {
                      const fg = graphComponentRef.current;
                      if (fg && typeof (fg as any).d3AlphaTarget === 'function') (fg as any).d3AlphaTarget(0);
                    }}
                    onChange={(e) => setNodeSettings(prev => ({
                      ...prev,
                      [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], linkStrength: parseFloat(e.target.value) }
                    }))}
                    style={{ width: '100%', accentColor: '#ff00ff' }}
                  />
                </div>
              </div>

              <div style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', opacity: 0.8, marginBottom: '5px' }}>
                  <span>Node Scale</span>
                  <span>{(nodeSettings[contextMenu.nodeId]?.sizeMultiplier || 1).toFixed(1)}x</span>
                </div>
                <input
                  type="range" min="0.5" max="5" step="0.1"
                  value={nodeSettings[contextMenu.nodeId]?.sizeMultiplier || 1}
                  onChange={(e) => setNodeSettings(prev => ({
                    ...prev,
                    [contextMenu.nodeId]: { ...prev[contextMenu.nodeId], sizeMultiplier: parseFloat(e.target.value) }
                  }))}
                  style={{ width: '100%', accentColor: '#ffcc00' }}
                />
              </div>

              <button
                onClick={() => setNodeSettings(prev => {
                  const next = { ...prev };
                  delete next[contextMenu.nodeId];
                  return next;
                })}
                style={{
                  marginTop: '10px',
                  background: 'rgba(255,100,100,0.1)',
                  border: '1px solid rgba(255,100,100,0.3)',
                  color: '#ff6666',
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontWeight: 600,
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,100,100,0.2)'}
                onMouseOut={(e) => e.currentTarget.style.background = 'rgba(255,100,100,0.1)'}
              >
                Reset to Defaults
              </button>
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
