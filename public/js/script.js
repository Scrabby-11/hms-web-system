document.addEventListener('DOMContentLoaded', () => {
    // API config
    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const API_BASE = isLocalhost ? 'http://localhost:5333/api' : '/api';

    // State
    let doctorsData = [];
    let patientsData = [];

    // DOM Elements
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.view-section');
    const pageTitle = document.getElementById('pageTitle');
    
    const modal = document.getElementById('appointmentModal');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const appointmentForm = document.getElementById('appointmentForm');

    // Initialize
    init();

    function init() {
        setupNavigation();
        setupModal();
        fetchAllData();
    }

    // --- Navigation Logic ---
    function setupNavigation() {
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                // Update active state on nav
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');

                // Switch section
                const targetId = item.getAttribute('data-target');
                sections.forEach(sec => sec.style.display = 'none');
                document.getElementById(targetId).style.display = 'block';

                // Update Title
                pageTitle.textContent = item.textContent.trim();
            });
        });
    }

    // --- Modal Logic ---
    function setupModal() {
        openModalBtn.onclick = () => {
            modal.style.display = "block";
            populateSelects();
        };

        closeModalBtn.onclick = () => {
            modal.style.display = "none";
            document.getElementById('formMsg').textContent = '';
            appointmentForm.reset();
        };

        window.onclick = (event) => {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        };

        appointmentForm.onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('submitAppointmentBtn');
            const msg = document.getElementById('formMsg');
            btn.disabled = true;
            btn.textContent = 'Booking...';

            const payload = {
                patient_id: document.getElementById('patientSelect').value,
                doctor_id: document.getElementById('doctorSelect').value,
                date: document.getElementById('appointmentDate').value,
                time: document.getElementById('appointmentTime').value
            };

            try {
                const res = await fetch(`${API_BASE}/appointments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                
                if (data.success) {
                    msg.style.color = '#34D399';
                    msg.textContent = 'Appointment booked successfully!';
                    setTimeout(() => {
                        modal.style.display = "none";
                        appointmentForm.reset();
                        msg.textContent = '';
                        // Refresh data
                        fetchDashboardData();
                        fetchAppointments();
                    }, 1500);
                } else {
                    msg.style.color = '#F87171';
                    msg.textContent = data.error || 'Failed to book appointment.';
                }
            } catch (err) {
                msg.style.color = '#F87171';
                msg.textContent = 'Network error occurred.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Book Appointment';
            }
        };
    }

    function populateSelects() {
        const pSelect = document.getElementById('patientSelect');
        const dSelect = document.getElementById('doctorSelect');
        
        pSelect.innerHTML = '<option value="">Select a patient...</option>' + 
            patientsData.map(p => `<option value="${p.patient_id}">${p.name} (ID: ${p.patient_id})</option>`).join('');
            
        dSelect.innerHTML = '<option value="">Select a doctor...</option>' + 
            doctorsData.map(d => `<option value="${d.doctor_id}">Dr. ${d.doctor_name} (${d.specialization})</option>`).join('');
    }

    // --- Data Fetching ---
    function fetchAllData() {
        fetchDashboardData();
        fetchDoctors();
        fetchPatients();
        fetchAppointments();
    }

    async function fetchDashboardData() {
        try {
            const [statsRes, apptRes] = await Promise.all([
                fetch(`${API_BASE}/dashboard-stats`).then(res => res.json()).catch(() => ({error: true})),
                fetch(`${API_BASE}/appointments?limit=5`).then(res => res.json()).catch(() => ({error: true}))
            ]);
            renderStats(statsRes);
            renderDashboardAppointments(apptRes);
        } catch (error) {
            console.error("Dashboard error:", error);
        }
    }

    async function fetchDoctors() {
        try {
            const res = await fetch(`${API_BASE}/doctors`).then(r => r.json());
            if (res.doctors) {
                doctorsData = res.doctors;
                renderDoctorsTable(res.doctors);
                renderDashboardDoctors(res.doctors.slice(0, 5));
            }
        } catch (err) {
            console.error("Doctors error:", err);
        }
    }

    async function fetchPatients() {
        try {
            const res = await fetch(`${API_BASE}/patients`).then(r => r.json());
            if (res.patients) {
                patientsData = res.patients;
                renderPatientsTable(res.patients);
            }
        } catch (err) {
            console.error("Patients error:", err);
        }
    }

    async function fetchAppointments() {
        try {
            const res = await fetch(`${API_BASE}/appointments`).then(r => r.json());
            if (res.appointments) {
                renderAppointmentsTable(res.appointments);
            }
        } catch (err) {
            console.error("Appointments error:", err);
        }
    }

    // --- Rendering Logic ---
    function renderStats(data) {
        const grid = document.getElementById('statsGrid');
        if (data.error || typeof data.error === 'string') {
            grid.innerHTML = `<div class="stat-card" style="grid-column: 1/-1; text-align: center; color: #F87171;">
                Failed to connect to Database. Please ensure backend is running.
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

    function renderDashboardDoctors(doctors) {
        const container = document.getElementById('dashboardDoctorsList');
        if (!doctors || doctors.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No doctors found.</p>`;
            return;
        }
        container.innerHTML = doctors.map(doc => `
            <div class="list-item">
                <div>
                    <div class="item-main">Dr. ${doc.doctor_name}</div>
                    <div class="item-sub">${doc.specialization || doc.department_name || 'General'}</div>
                </div>
                <div class="status-badge" style="background: rgba(139, 92, 246, 0.2); color: #A78BFA;">ID: ${doc.doctor_id}</div>
            </div>
        `).join('');
    }

    function renderDashboardAppointments(data) {
        const container = document.getElementById('dashboardAppointmentsList');
        if (data.error || !data.appointments || data.appointments.length === 0) {
            container.innerHTML = `<p style="color: var(--text-muted); padding: 1rem;">No recent appointments.</p>`;
            return;
        }
        container.innerHTML = data.appointments.map(appt => {
            let statusClass = 'status-scheduled';
            if(appt.status) {
                const s = appt.status.toLowerCase();
                if(s.includes('complet')) statusClass = 'status-completed';
                if(s.includes('cancel')) statusClass = 'status-cancelled';
                if(s.includes('pending')) statusClass = 'status-pending';
            }
            return `
            <div class="list-item">
                <div>
                    <div class="item-main">${appt.patient_name} <span style="font-size:0.8rem;font-weight:normal;color:var(--text-muted)">with Dr. ${appt.doctor_name}</span></div>
                    <div class="item-sub">${appt.date || 'No Date'} at ${appt.time || 'N/A'}</div>
                </div>
                <div class="status-badge ${statusClass}">${appt.status || 'Scheduled'}</div>
            </div>
            `;
        }).join('');
    }

    function renderDoctorsTable(doctors) {
        const tbody = document.getElementById('doctorsTableBody');
        if (doctors.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center">No doctors found</td></tr>`;
            return;
        }
        tbody.innerHTML = doctors.map(d => `
            <tr>
                <td>#${d.doctor_id}</td>
                <td><strong>Dr. ${d.doctor_name}</strong></td>
                <td>${d.specialization || '-'}</td>
                <td>${d.department_name || '-'}</td>
                <td>${d.phone_no || '-'}</td>
            </tr>
        `).join('');
    }

    function renderPatientsTable(patients) {
        const tbody = document.getElementById('patientsTableBody');
        if (patients.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center">No patients found</td></tr>`;
            return;
        }
        tbody.innerHTML = patients.map(p => `
            <tr>
                <td>#${p.patient_id}</td>
                <td><strong>${p.name}</strong></td>
                <td>${p.gender || '-'}</td>
                <td>${p.dob || '-'}</td>
                <td>${p.phone_no || '-'}</td>
                <td>${p.address || '-'}</td>
            </tr>
        `).join('');
    }

    function renderAppointmentsTable(appointments) {
        const tbody = document.getElementById('appointmentsTableBody');
        if (appointments.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align:center">No appointments found</td></tr>`;
            return;
        }
        tbody.innerHTML = appointments.map(a => {
            let statusClass = 'status-scheduled';
            if(a.status) {
                const s = a.status.toLowerCase();
                if(s.includes('complet')) statusClass = 'status-completed';
                if(s.includes('cancel')) statusClass = 'status-cancelled';
                if(s.includes('pending')) statusClass = 'status-pending';
            }
            return `
            <tr>
                <td>#${a.appointment_id}</td>
                <td>${a.patient_name}</td>
                <td>Dr. ${a.doctor_name}</td>
                <td>${a.date || '-'}</td>
                <td>${a.time || '-'}</td>
                <td><span class="status-badge ${statusClass}">${a.status || 'Scheduled'}</span></td>
            </tr>
            `;
        }).join('');
    }
});
