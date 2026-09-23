import { NavLink, useNavigate, useParams, useLocation } from 'react-router-dom';
import { useTerms, getModeIcon } from '../../utils/terminology';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const params = useParams();
    const { user, loading, logout } = useAuth();   // ✅ loading bhi lo
    const t = useTerms();

    // ═══════════════════════════════════════════════════════════════
    // ✅ CRITICAL FIX: Loading ya user null par kuch render na karo
    // Ye flash rokta hai jab /auth/me call ho rahi ho
    // ═══════════════════════════════════════════════════════════════
    if (loading || !user) {
        return (
            <div
                style={{
                    width: '250px',
                    backgroundColor: '#1e293b',
                    color: 'white',
                    height: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'fixed',
                    left: 0,
                    top: 0,
                    alignItems: 'center',
                    justifyContent: 'center',
                }}
            >
                <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                    <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔒</div>
                    <div style={{ fontSize: '13px' }}>Loading...</div>
                </div>
            </div>
        );
    }

    // ═══════════════════════════════════════════════════════════════
    // ✅ Ab safe hai — user maujood hai
    // ═══════════════════════════════════════════════════════════════
    const role = user.role || 'admin';

    let schoolSlug = params.schoolSlug || null;

    if (!schoolSlug) {
        const pathParts = location.pathname.split('/').filter(Boolean);
        if (
            pathParts.length >= 3 &&
            !['superadmin', 'admin', 'teacher', 'student', 'login'].includes(pathParts[0])
        ) {
            schoolSlug = pathParts[0];
        }
    }

    const prefix = schoolSlug ? `/${schoolSlug}` : '';
    const instituteType = user.institute_type || 'school';
    const modeIcon = getModeIcon(instituteType);

    const superAdminMenu = [
        { name: '🏫 Schools Management', path: '/superadmin/schools' },
    ];

    const adminMenu = [
        { name: 'Dashboard', path: `${prefix}/admin/dashboard` },
        { name: t.students, path: `${prefix}/admin/students` },
        { name: t.classes, path: `${prefix}/admin/classes` },
        { name: t.sections, path: `${prefix}/admin/sections` },
        { name: t.subjects, path: `${prefix}/admin/subjects` },
        { name: t.teachers, path: `${prefix}/admin/teachers` },
        { name: t.attendance, path: `${prefix}/admin/attendance` },
        { name: t.fees, path: `${prefix}/admin/fees` },
        { name: 'Concession', path: `${prefix}/admin/concession` },
        { name: t.homework, path: `${prefix}/admin/homework` },
        { name: 'Assignments', path: `${prefix}/admin/assignments` },
        { name: t.exams, path: `${prefix}/admin/exams` },
        { name: t.results, path: `${prefix}/admin/results` },
        { name: t.noticeBoard, path: `${prefix}/admin/notice-board` },
        { name: t.studyMaterial, path: `${prefix}/admin/study-material` },
        { name: t.guardians, path: `${prefix}/admin/guardians` },
        { name: t.timetable, path: `${prefix}/admin/timetable` },
        { name: 'Academic Years', path: `${prefix}/admin/academic-years` },
        { name: 'Settings', path: `${prefix}/admin/settings` },
        { name: 'Analytics', path: `${prefix}/admin/analytics` },
        { name: '📢 Broadcast', path: `${prefix}/admin/broadcast` },
    ];

    const teacherMenu = [
        { name: 'Dashboard', path: `${prefix}/teacher/dashboard` },
        { name: `My ${t.classes}`, path: `${prefix}/teacher/my-classes` },
        { name: `My ${t.students}`, path: `${prefix}/teacher/my-students` },
        { name: `Mark ${t.attendance}`, path: `${prefix}/teacher/mark-attendance` },
        { name: t.homework, path: `${prefix}/teacher/homework` },
        { name: 'Assignments', path: `${prefix}/teacher/assignments` },
        { name: `${t.marks} Entry`, path: `${prefix}/teacher/marks-entry` },
        { name: t.timetable, path: `${prefix}/teacher/timetable` },
        { name: t.studyMaterial, path: `${prefix}/teacher/study-material` },
        { name: t.noticeBoard, path: `${prefix}/teacher/notice-board` },
        { name: '💬 Message Parent', path: `${prefix}/teacher/message-parent` },
    ];

    const studentMenu = [
        { name: 'Dashboard', path: `${prefix}/student/dashboard` },
        { name: `My ${t.attendance}`, path: `${prefix}/student/my-attendance` },
        { name: `My ${t.homework}`, path: `${prefix}/student/my-homework` },
        { name: 'My Assignments', path: `${prefix}/student/my-assignments` },
        { name: `My ${t.timetable}`, path: `${prefix}/student/my-timetable` },
        { name: `My ${t.results}`, path: `${prefix}/student/my-results` },
        { name: `My ${t.fees}`, path: `${prefix}/student/my-fees` },
        { name: t.studyMaterial, path: `${prefix}/student/study-material` },
        { name: t.noticeBoard, path: `${prefix}/student/notice-board` },
    ];

    let menuItems = [];
    let roleLabel = 'Admin';

    if (role === 'super_admin') {
        menuItems = superAdminMenu;
        roleLabel = 'Super Admin';
    } else if (role === 'admin') {
        menuItems = adminMenu;
        roleLabel = 'Admin';
    } else if (role === 'teacher') {
        menuItems = teacherMenu;
        roleLabel = 'Teacher';
    } else if (role === 'student') {
        menuItems = studentMenu;
        roleLabel = 'Student';
    } else {
        menuItems = adminMenu;
        roleLabel = 'Admin';
    }

    const handleLogout = async () => {
        await logout();
    };

    return (
        <div
            style={{
                width: '250px',
                backgroundColor: '#1e293b',
                color: 'white',
                height: '100vh',
                display: 'flex',
                flexDirection: 'column',
                position: 'fixed',
                left: 0,
                top: 0,
            }}
        >
            <div style={{ padding: '20px', borderBottom: '1px solid #334155', flexShrink: 0 }}>
                <h2 style={{ margin: 0, fontSize: '20px' }}>
                    {modeIcon} {user.school_name || 'School ERP'}
                </h2>
                <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
                    {roleLabel} Panel
                </p>
            </div>

            <nav
                style={{
                    flex: 1,
                    padding: '12px',
                    overflowY: 'auto',
                    overflowX: 'hidden',
                }}
            >
                {menuItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        style={({ isActive }) => ({
                            display: 'block',
                            padding: '10px 14px',
                            marginBottom: '4px',
                            borderRadius: '8px',
                            textDecoration: 'none',
                            color: 'white',
                            fontSize: '14px',
                            backgroundColor: isActive ? '#4f46e5' : 'transparent',
                        })}
                    >
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            <div style={{ padding: '12px', borderTop: '1px solid #334155', flexShrink: 0 }}>
                <button
                    onClick={handleLogout}
                    style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: 'none',
                        backgroundColor: '#dc2626',
                        color: 'white',
                        cursor: 'pointer',
                        fontSize: '14px',
                        textAlign: 'left',
                    }}
                >
                    🚪 Logout
                </button>
            </div>
        </div>
    );
};

export default Sidebar;