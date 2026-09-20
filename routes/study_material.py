import { useState, useEffect } from 'react';
import api from '../../api/axios';

const StudentStudyMaterial = () => {
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchMaterials();
    }, []);

    const fetchMaterials = async () => {
        try {
            const meRes = await api.get('/auth/me');
            const classId = meRes.data.class_id;

            if (!classId) {
                setError('Class not assigned');
                setLoading(false);
                return;
            }

            const res = await api.get(`/study-material/class/${classId}`);
            const data = Array.isArray(res.data) ? res.data : [];
            setMaterials(data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to load study material');
            setMaterials([]);
        } finally {
            setLoading(false);
        }
    };

    const getFileIcon = (url) => {
        if (!url) return '📄';
        const ext = url.split('.').pop().toLowerCase();
        if (ext === 'pdf') return '📕';
        if (['jpg', 'jpeg', 'png'].includes(ext)) return '🖼️';
        if (['doc', 'docx'].includes(ext)) return '📘';
        return '📄';
    };

    if (loading) return <div style={{ padding: '60px', textAlign: 'center', color: '#718096' }}>Loading...</div>;

    return (
        <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif' }}>
            <div style={{ marginBottom: '30px' }}>
                <h1 style={{ fontSize: '32px', color: '#1a202c', margin: '0 0 8px 0' }}>Study Material</h1>
                <p style={{ color: '#718096', margin: 0 }}>Notes and resources for your class</p>
            </div>

            {error && (
                <div style={{ padding: '20px 24px', borderRadius: '12px', background: '#fed7d7', color: '#c53030', marginBottom: '20px' }}>
                    ⚠️ {error}
                </div>
            )}

            {materials.length === 0 ? (
                <div style={{ backgroundColor: 'white', borderRadius: '16px', padding: '60px 20px', textAlign: 'center', boxShadow: '0 4px 20px rgba(0,0,0,0.08)' }}>
                    <div style={{ fontSize: '64px', marginBottom: '16px' }}>📚</div>
                    <p style={{ color: '#718096' }}>No study material yet</p>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                    {materials.map((m) => (
                        <div key={m.id} style={{ backgroundColor: 'white', borderRadius: '16px', padding: '20px', boxShadow: '0 4px 20px rgba(0,0,0,0.08)', borderTop: '4px solid #667eea' }}>
                            <div style={{ fontSize: '40px', marginBottom: '12px' }}>{getFileIcon(m.file_path)}</div>
                            <h3 style={{ margin: '0 0 8px 0', color: '#1a202c' }}>{m.title}</h3>
                            <p style={{ color: '#718096', margin: '0 0 12px 0', fontSize: '14px', lineHeight: '1.5' }}>{m.description}</p>
                            {m.file_path && (
                                <a href={m.file_path} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-block', padding: '10px 20px', backgroundColor: '#48bb78', color: 'white', borderRadius: '8px', textDecoration: 'none', fontSize: '14px', fontWeight: '600' }}>
                                    📥 Download
                                </a>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default StudentStudyMaterial;