import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Clock, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../api';
import { VideoProject } from '../types';
import { CreateProject } from '../components/CreateProject';

export function Dashboard() {
    const [projects, setProjects] = useState<VideoProject[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProjects();
        const interval = setInterval(loadProjects, 5000); // Auto refresh
        return () => clearInterval(interval);
    }, []);

    const loadProjects = async () => {
        try {
            const data = await api.getProjects();
            setProjects(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
                <div>
                    <h1>Your Projects</h1>
                    <p>Manage and create your AI videos</p>
                </div>
            </header>

            <CreateProject />

            <div style={{ marginTop: '40px' }}>
                <h2>Recent Activity</h2>
                {projects.length === 0 && !loading && (
                    <p>No projects yet. Start by uploading a video!</p>
                )}

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {projects.map(p => (
                        <Link to={`/projects/${p.id}`} key={p.id} style={{ textDecoration: 'none' }}>
                            <div className="card project-card" style={{ cursor: 'pointer', height: '100%' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <h3 style={{ marginTop: 0, color: 'white' }}>{p.title}</h3>
                                    <span className={`status-badge status-${p.status}`}>
                                        {p.status_display}
                                    </span>
                                </div>
                                <p style={{ fontSize: '0.9rem', marginBottom: '20px' }}>
                                    {new Date(p.created_at).toLocaleDateString()}
                                </p>

                                {p.status === 'completed' && <div style={{ color: 'var(--success)', display: 'flex', gap: '6px' }}><CheckCircle size={16} /> Ready for Download</div>}
                                {p.status === 'failed' && <div style={{ color: 'var(--danger)', display: 'flex', gap: '6px' }}><AlertCircle size={16} /> Failed</div>}
                                {p.status === 'analyzing' && <div style={{ color: 'var(--accent)', display: 'flex', gap: '6px' }}><Clock size={16} /> Analyzing...</div>}
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
}
