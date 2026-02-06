import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileVideo, Plus } from 'lucide-react';
import { api } from '../api';

export function CreateProject() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const navigate = useNavigate();

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const title = file.name.replace(/\.[^/.]+$/, "");
            const project = await api.createProject(title, file);
            navigate(`/projects/${project.id}`);
        } catch (err) {
            console.error("Upload failed", err);
            alert("Upload failed. Check console.");
        }
    };

    return (
        <div className="create-project-card card" style={{ textAlign: 'center', padding: '40px', borderStyle: 'dashed' }}>
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="video/*"
                style={{ display: 'none' }}
            />
            <div style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                <Upload size={48} />
            </div>
            <h2>Create New Project</h2>
            <p>Upload a talking head video to start the AI magic.</p>

            <button className="btn btn-upload" onClick={() => fileInputRef.current?.click()} style={{ marginTop: '20px' }}>
                <Plus size={18} /> Upload Video
            </button>
        </div>
    );
}
