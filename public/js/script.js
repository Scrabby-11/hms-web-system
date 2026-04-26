document.addEventListener('DOMContentLoaded', () => {
    // Determine API Base URL based on environment
    const API_BASE = '/api';

    fetchDashboardData();

    async function fetchDashboardData() {
        try {
            const [statsRes, doctorsRes, appointmentsRes] = await Promise.all([
                fetch(`${API_BASE}/dashboard-stats`).then(res => res.json()).catch(() => ({error: true})),
                fetch(`${API_BASE}/doctors`).then(res => res.json()).catch(() => ({error: true})),
                fetch(`${API_BASE}/appointments`).then(res => res.json()).catch(() => ({error: true}))
            ]);

            renderStats(statsRes);
            renderDoctors(doctorsRes);
            renderAppointments(appointmentsRes);
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        }
    }

    function renderStats(data) {
        const grid = document.getElementById('statsGrid');
        if (data.error || data.error !== undefined && typeof data.error === 'string') {
            grid.innerHTML = `<div class="stat-card" style="grid-column: 1/-1; text-align: center; color: #F87171;">
                Failed to connect to Database. Please ensure MySQL is running and configured locally, or environment variables are set for production.
            </div>`;
            return;
        }

        grid.innerHTML = `
            <div class="stat-card">
                <div class="stat-icon">🤒</div>
                <div class="stat-value">${data.patients || 0}</div>
                <div class="stat-label">Total Patients</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👨‍⚕️</div>
                <div class="stat-value">${data.doctors || 0}</div>
                <div class="stat-label">Total Doctors</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📅</div>
                <div class="stat-value">${data.appointments || 0}</div>
                <div class="stat-label">Appointments</div>
            </div>
        `;
    }

    function renderDoctors(data) {
        const container = document.getElementById('doctorsList');
        if (data.error || !data.doctors) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">Unable to load doctors.</p>`;
            return;
        }

        if (data.doctors.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No doctors found.</p>`;
            return;
        }

        container.innerHTML = data.doctors.map(doc => `
            <div class="list-item">
                <div>
                    <div class="item-main">${doc.doctor_name}</div>
                    <div class="item-sub">${doc.specialization || doc.department_name || 'General'}</div>
                </div>
                <div class="status-badge" style="background: rgba(139, 92, 246, 0.2); color: #A78BFA;">ID: ${doc.doctor_id}</div>
            </div>
        `).join('');
    }

    function renderAppointments(data) {
        const container = document.getElementById('appointmentsList');
        if (data.error || !data.appointments) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">Unable to load appointments.</p>`;
            return;
        }

        if (data.appointments.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No recent appointments.</p>`;
            return;
        }

        container.innerHTML = data.appointments.map(appt => {
            let statusClass = 'status-scheduled';
            if(appt.status) {
                const s = appt.status.toLowerCase();
                if(s.includes('complet')) statusClass = 'status-completed';
                if(s.includes('cancel')) statusClass = 'status-cancelled';
            }

            return `
            <div class="list-item">
                <div>
                    <div class="item-main">${appt.patient_name} <span style="color:var(--text-muted); font-size:0.8rem; font-weight:normal;">with</span> Dr. ${appt.doctor_name}</div>
                    <div class="item-sub">${appt.date || 'No Date'}</div>
                </div>
                <div class="status-badge ${statusClass}">${appt.status || 'Scheduled'}</div>
            </div>
            `;
        }).join('');
    }
});
