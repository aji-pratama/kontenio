import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Play, Wand2, Download, Layers, Image as ImageIcon } from 'lucide-react';
import { api } from '../api';
import { VideoProject, VideoSegment } from '../types';

export function Workspace() {
    const { id } = useParams<{ id: string }>();
    const projectId = parseInt(id || '0');

    const [project, setProject] = useState<VideoProject | null>(null);
    const [segments, setSegments] = useState<VideoSegment[]>([]);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [rendering, setRendering] = useState(false);

    const loadData = useCallback(async () => {
        try {
            const p = await api.getProject(projectId);
            setProject(p);

            // If ready or later, load segments
            if (['ready', 'rendering', 'completed'].includes(p.status)) {
                const s = await api.getSegments(projectId);
                setSegments(s);
            }

            // Update local loading states based on status
            if (p.status === 'analyzing') setAnalyzing(true);
            else setAnalyzing(false);

            if (p.status === 'rendering') setRendering(true);
            else setRendering(false);

        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 3000);
        return () => clearInterval(interval);
    }, [loadData]);

    const handleAnalyze = async () => {
        setAnalyzing(true);
        try {
            await api.analyzeProject(projectId);
        } catch (e) {
            alert("Analysis failed start");
            setAnalyzing(false);
        }
    };

    const handleRender = async () => {
        setRendering(true);
        try {
            await api.renderProject(projectId);
        } catch (e) {
            alert("Render failed start");
            setRendering(false);
        }
    };

    const handleSegmentUpdate = async (segId: number, field: string, value: any) => {
        // Optimistic update
        setSegments(prev => prev.map(s => s.id === segId ? { ...s, [field]: value } : s));
        try {
            await api.updateSegment(segId, { [field]: value });
        } catch (e) {
            console.error("Update failed", e);
            loadData(); // Revert
        }
    };

    if (loading || !project) return <div className="container"><div className="loader"></div> Loading...</div>;

    return (
        <div className="container">
            <Link to="/" className="btn btn-secondary" style={{ marginBottom: '20px' }}><ArrowLeft size={16} /> Back</Link>

            <header className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <span className={`status-badge status-${project.status}`} style={{ marginBottom: '8px', display: 'inline-block' }}>{project.status_display}</span>
                    <h1 style={{ fontSize: '1.8rem', margin: 0 }}>{project.title}</h1>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>{project.progress_message}</p>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                    {/* Phase 1 Trigger */}
                    {(project.status === 'draft' || project.status === 'failed') && (
                        <button className="btn btn-primary" onClick={handleAnalyze} disabled={analyzing}>
                            {analyzing ? <div className="loader" style={{ width: 16, height: 16, borderTopColor: 'white' }}></div> : <Wand2 size={18} />}
                            {analyzing ? ' Analyzing...' : ' Analyze with AI'}
                        </button>
                    )}

                    {/* Phase 3 Trigger */}
                    {project.status === 'ready' && (
                        <button className="btn btn-primary" onClick={handleRender} disabled={rendering}>
                            {rendering ? <div className="loader" style={{ width: 16, height: 16, borderTopColor: 'white' }}></div> : <Play size={18} />}
                            {rendering ? ' Rendering...' : ' Generate Final Video'}
                        </button>
                    )}

                    {project.status === 'completed' && project.output_video_url && (
                        <a href={project.output_video_url} download className="btn btn-primary" style={{ background: 'var(--success)' }}>
                            <Download size={18} /> Download Video
                        </a>
                    )}
                </div>
            </header>

            {/* Main Workspace Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '20px' }}>

                {/* Left: Editor / Review Table */}
                <div>
                    {project.status === 'ready' ? (
                        <div className="card">
                            <h2><Layers size={20} style={{ verticalAlign: 'middle' }} /> Segment Editor</h2>
                            <p style={{ fontSize: '0.9rem' }}>Review AI generated assets and tweak the flow.</p>

                            <table className="review-table">
                                <thead>
                                    <tr>
                                        <th style={{ width: '60px' }}>Time</th>
                                        <th>Transcript & Asset</th>
                                        <th style={{ width: '120px' }}>Layout</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {segments.map(seg => (
                                        <tr key={seg.id}>
                                            <td>
                                                <div style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>{seg.start_time.toFixed(1)}s</div>
                                                <div style={{ fontSize: '0.8rem', color: '#666' }}>{(seg.end_time - seg.start_time).toFixed(1)}s</div>
                                            </td>
                                            <td>
                                                <textarea
                                                    rows={2}
                                                    value={seg.transcript}
                                                    onChange={(e) => handleSegmentUpdate(seg.id, 'transcript', e.target.value)}
                                                    style={{ marginBottom: '10px' }}
                                                />

                                                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                                                    {seg.asset_file ? (
                                                        <img src={seg.asset_file} alt="Asset" style={{ width: '60px', height: '60px', objectFit: 'cover', borderRadius: '8px' }} />
                                                    ) : (
                                                        <div style={{ width: '60px', height: '60px', background: '#222', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                                            <ImageIcon size={20} color="#444" />
                                                        </div>
                                                    )}

                                                    <select
                                                        value={seg.asset_type}
                                                        onChange={(e) => handleSegmentUpdate(seg.id, 'asset_type', e.target.value)}
                                                        style={{ width: 'auto', padding: '6px' }}
                                                    >
                                                        <option value="ai_image">AI Image</option>
                                                        <option value="video_clip">Video Clip</option>
                                                        <option value="user_upload">Upload...</option>
                                                    </select>
                                                    <div style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>{seg.animation_type}</div>
                                                </div>
                                            </td>
                                            <td>
                                                <select
                                                    value={seg.layout_event}
                                                    onChange={(e) => handleSegmentUpdate(seg.id, 'layout_event', e.target.value)}
                                                >
                                                    <option value="split">Split</option>
                                                    <option value="bottom_full">Full Face</option>
                                                    <option value="top_full">Full Visual</option>
                                                </select>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
                            {project.status === 'draft' && <p>Click "Analyze with AI" to generate segments.</p>}
                            {project.status === 'analyzing' && <div className="loader"></div>}
                        </div>
                    )}
                </div>

                {/* Right: Preview */}
                <div>
                    <div className="card" style={{ position: 'sticky', top: '20px' }}>
                        <h2>Preview</h2>
                        <div style={{ aspectRatio: '9/16', background: 'black', borderRadius: '8px', overflow: 'hidden' }}>
                            {project.output_video_url ? (
                                <video src={project.output_video_url} controls style={{ width: '100%', height: '100%' }} />
                            ) : project.raw_video_url ? (
                                <video src={project.raw_video_url} controls style={{ width: '100%', height: '100%' }} />
                            ) : (
                                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#444' }}>
                                    No Preview
                                </div>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
