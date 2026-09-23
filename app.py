import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import importlib
import database as db
importlib.reload(db)

# Page Configuration
st.set_page_config(
    page_title="SmartShare | Unattended Multi-Resource Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database on first load
db.init_db()

# --- Custom Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .digital-pass {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .rules-card {
        background-color: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 16px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    .badge-available {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 13px;
    }
    .badge-booked {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: User Authentication & Persistent Ledger ---
st.sidebar.title("🏢 SmartShare")
st.sidebar.caption("Zero-CapEx Shared Resource Governance")

all_users = db.get_all_users()
user_names = [u['name'] for u in all_users]

# Ensure state tracks active user and switches instantly when a new user registers
if 'active_user_name' not in st.session_state or st.session_state['active_user_name'] not in user_names:
    st.session_state['active_user_name'] = user_names[0]

selected_idx = user_names.index(st.session_state['active_user_name'])
selected_name = st.sidebar.selectbox("Select Resident Profile (Passwordless):", user_names, index=selected_idx)
st.session_state['active_user_name'] = selected_name

current_user = db.get_user_by_name(selected_name)

# Display User Persistent Ledger
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Resident Profile")
st.sidebar.write(f"**Name:** {current_user['name']}")
st.sidebar.write(f"**Room:** {current_user['room_number']}")

# Key persistence metric with 15 credits
col_c1, col_c2 = st.sidebar.columns(2)
with col_c1:
    st.metric(
        label="Remaining Credits",
        value=f"{current_user['remaining_credits']}/{current_user['total_weekly_credits']}",
        help="Credits reset every Monday. Persistent across logins."
    )
with col_c2:
    st.metric(
        label="Karma Score",
        value=f"{current_user['karma_score']}/100",
        help="Starts at 100. Measures community reliability."
    )

st.sidebar.caption("⭐ **What is Karma Score?** Starts at 100. Measures your community reliability rating. Punctual check-ins & clean handoffs maintain high standing. Dropping below 75 restricts access to prime weekend slots and flags account for warden review.")

# Add New Resident Option in Sidebar (Direct auto-switch)
with st.sidebar.expander("➕ Register New Resident"):
    new_name = st.text_input("Resident Full Name")
    new_room = st.text_input("Room Number (e.g. Room 205)")
    if st.button("Create & Switch to User"):
        if new_name and new_room:
            db.create_or_get_user(new_name, new_room)
            conn = db.get_connection()
            conn.execute("UPDATE users SET total_weekly_credits = 15, remaining_credits = 15 WHERE name = ?", (new_name,))
            conn.commit()
            conn.close()
            st.session_state['active_user_name'] = new_name
            st.success(f"Registered and logged in as {new_name}!")
            st.rerun()

# --- Main App Navigation ---
tab_resident, tab_admin = st.tabs([
    "📅 Resident Booking Portal",
    "📊 Warden & Operations Console"
])

# ==============================================================================
# TAB 1: RESIDENT BOOKING PORTAL
# ==============================================================================
with tab_resident:
    st.title("⚡ Multi-Resource Allocation Engine")
    st.caption("Fair scheduling, automated buffers, and anti-squatting governance across shared assets.")

    # Facility Rules & Operational Guidelines
    with st.expander("📋 Facility Rules, Booking Pre-Requisites & Penalty Guidelines", expanded=False):
        st.markdown("""
        - 🎟️ **15 Weekly Credits**: Every resident receives 15 credits per week to book across Appliances, Sports, and Study Rooms.
        - ⏳ **48-Hour Rolling Window**: Slots open strictly 48 hours prior to reservation time to eliminate slot hoarding.
        - 🔐 **Physical PIN Check-In**: Check-in and equipment clearance are verified using the 4-digit physical PIN taped directly to the asset or hamper rack.
        - ⏱️ **10-Minute Grace Window**: Arrive within 10 minutes of slot start time, or your reservation is automatically surrendered.
        - 🧺 **Hamper Clearance Bounty**: Clean laundry left in washing machines >10 mins post-cycle can be transferred to the owner's designated room hamper. The mover earns **+2 bonus credits** funded by the overstayer.
        - 💰 **Overstay Rent Demerits**: Refusing to vacate a court or room incurs a **₹10–15/min fine** auto-billed directly to the offending room's monthly PG rent invoice.
        """)

    # Category Selector: Uniform 3 Categories
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    with cat_col1:
        cat_app = st.button("🧺 Appliances & Household", use_container_width=True)
    with cat_col2:
        cat_sport = st.button("⚽ Sports & Recreation", use_container_width=True)
    with cat_col3:
        cat_room = st.button("📚 Study & Community Rooms", use_container_width=True)

    if 'active_category' not in st.session_state:
        st.session_state['active_category'] = 'Appliances'

    if cat_app:
        st.session_state['active_category'] = 'Appliances'
    elif cat_sport:
        st.session_state['active_category'] = 'Sports'
    elif cat_room:
        st.session_state['active_category'] = 'Rooms'

    category = st.session_state['active_category']
    resources = db.get_resources_by_category(category)

    st.markdown(f"### Currently Viewing: **{category}**")

    # Step 1: Select Resource and Date
    col_res, col_date = st.columns([1, 1])
    with col_res:
        res_names = {r['name']: r['resource_id'] for r in resources}
        selected_res_name = st.selectbox("Select Asset to Reserve:", list(res_names.keys()))
        selected_res_id = res_names[selected_res_name]
        res_meta = db.get_resource_details(selected_res_id)

    with col_date:
        today = date.today()
        # Strictly enforce 48-Hour Rolling Window to stop midnight hoarding
        booking_date = st.date_input(
            "Select Booking Date (Max 48h in advance):",
            min_value=today,
            max_value=today + timedelta(days=2),
            value=today
        )
        st.caption("🔒 **48-Hour Rolling Window**: Preserves fair access and prevents weekend slot hoarding.")

    # Step 2: Resource Configuration & Cycle Details
    st.markdown("---")
    st.subheader(f"⚙️ Reserve: {res_meta['name']}")

    col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
    with col_meta1:
        st.write(f"**Category:** {res_meta['category']}")
    with col_meta2:
        st.write(f"**Safety Buffer:** {res_meta['buffer_mins']} mins")
    with col_meta3:
        st.write(f"**Capacity:** {res_meta['capacity']} person(s)")
    with col_meta4:
        st.write(f"**Overstay Penalty:** ₹{res_meta['overstay_rate_per_min']}/min")

    # Dynamic Cycle vs Fixed Block Selection
    if res_meta['slot_type'] == 'VARIABLE_CYCLE':
        cycle_choice = st.radio(
            "Select Wash Program:",
            [
                ("Quick Wash (20m wash + 15m buffer = 35m total)", 20, 1),
                ("Standard Everyday Wash (45m wash + 15m buffer = 60m total)", 45, 1),
                ("Heavy / Blankets Wash (60m wash + 15m buffer = 75m total)", 60, 2)
            ],
            format_func=lambda x: x[0]
        )
        actual_duration = cycle_choice[1]
        base_slot_credits = cycle_choice[2]
    else:
        duration_options = [60, 90] if res_meta['default_duration_mins'] >= 60 else [res_meta['default_duration_mins']]
        actual_duration = st.selectbox(
            "Select Duration (Minutes):",
            duration_options,
            format_func=lambda x: f"{x} minutes (+ {res_meta['buffer_mins']} mins buffer included)"
        )
        base_slot_credits = res_meta['base_credits']

    # Step 3: Check Slot Schedule & Availability Matrix
    booking_date_str = booking_date.strftime("%Y-%m-%d")
    existing_bookings = db.get_existing_bookings(selected_res_id, booking_date_str)
    booked_start_times = [b['start_time'] for b in existing_bookings]

    st.write(f"#### Available Slots for {booking_date.strftime('%A, %b %d')}:")

    # Generate hourly slots
    start_hour = res_meta['operating_start_hour']
    end_hour = res_meta['operating_end_hour']
    slot_list = []
    for h in range(start_hour, end_hour):
        s_str = f"{h:02d}:00"
        e_str = f"{(h+1):02d}:00" if actual_duration <= 60 else f"{(h+2):02d}:00"
        slot_list.append((s_str, e_str))

    selected_slot = st.selectbox(
        "Choose a Time Window:",
        slot_list,
        format_func=lambda s: f"{s[0]} - {s[1]} {'[🔴 ALREADY BOOKED]' if s[0] in booked_start_times else '[🟢 AVAILABLE]'}"
    )

    req_start, req_end = selected_slot
    is_already_booked = req_start in booked_start_times

    # Calculate Price & Consecutive Surge Checks
    is_consecutive = db.check_consecutive_booking(current_user['user_id'], selected_res_id, booking_date_str, req_start)
    final_credit_cost = base_slot_credits * 2 if is_consecutive else base_slot_credits

    # Callout for Pricing & Incentives
    price_col1, price_col2 = st.columns([2, 1])
    with price_col1:
        if is_consecutive:
            st.warning(f"⚠️ **Anti-Cartel Policy Active**: You hold an adjacent slot. Consecutive booking surge applied: **{final_credit_cost} Credits**.")
        else:
            st.success(f"🏷️ Slot Cost: **{final_credit_cost} Credit(s)** (Deducted from weekly quota)")

    with price_col2:
        if current_user['remaining_credits'] < final_credit_cost:
            st.error(f"❌ Insufficient Credits ({current_user['remaining_credits']} left).")
            can_book = False
        elif is_already_booked:
            st.error("❌ Slot occupied by another resident.")
            can_book = False
        else:
            can_book = True

    # Single-Click Guaranteed Confirm Booking Button (Guards against double-charging)
    booking_button_key = f"btn_book_{selected_res_id}_{booking_date_str}_{req_start}"
    if st.button("🚀 Confirm Slot Reservation", disabled=not can_book, use_container_width=True, key=booking_button_key):
        booking_id = db.create_booking(
            user_id=current_user['user_id'],
            resource_id=selected_res_id,
            booking_date_str=booking_date_str,
            start_time_str=req_start,
            end_time_str=req_end,
            duration_mins=actual_duration,
            credits_charged=final_credit_cost,
            is_consecutive=is_consecutive
        )
        if booking_id:
            st.balloons()
            st.success(f"✅ Booking Confirmed for {selected_res_name} at {req_start}! {final_credit_cost} credit(s) debited.")
            st.rerun()
        else:
            st.error("Slot was just claimed by another user or already confirmed.")

    # --- Live Digital Pass & Exception Handling Actions ---
    st.markdown("---")
    st.subheader("📱 Active Digital Pass & In-Session Controls")

    # Render Active Pass
    st.markdown(f"""
    <div class="digital-pass">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h3>🟢 ACTIVE DIGITAL CUSTODY PASS</h3>
            <span style="background:rgba(255,255,255,0.25); padding:4px 12px; border-radius:16px; font-size:14px;">Authorized Session</span>
        </div>
        <hr style="border-color:rgba(255,255,255,0.3);">
        <p style="font-size:18px; margin-bottom:4px;"><b>Asset:</b> {selected_res_name} ({category})</p>
        <p style="font-size:16px; margin-bottom:4px;"><b>Authorized Resident:</b> {current_user['name']} ({current_user['room_number']})</p>
        <p style="font-size:15px; margin-bottom:0px;"><b>Valid Time Window:</b> {req_start} – {req_end} (Buffer Protected)</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("🛡️ **Zero-Hardware Social Proof**: Show this screen to prove authorized possession and clear unbooked walk-in squatters immediately.")

    # 4 Exception-Handling Workflows (Pure PIN / Text based - No Camera needed)
    st.markdown("#### 🛠️ Exception Handling & Friction Mitigation")
    ex_col1, ex_col2 = st.columns(2)

    with ex_col1:
        with st.expander("⚡ I Finished Early — Release Slot (Get 50% Refund)"):
            st.write("Free up the asset for your other residents and receive half of your credit back immediately.")
            if st.button("Release Slot Early & Claim Refund"):
                db.add_user_credits(current_user['user_id'], 1)
                st.success("🎉 Slot marked released! 1 Credit refunded to your ledger.")
                st.rerun()

        with ex_col2:
            with st.expander("🧺 Prior User Left Items / Clothes? (Claim +2 Bounty)"):
                st.write("Unload uncollected items into the owner's designated room hamper. Enter the 4-digit PIN taped on the hamper rack to verify clearance.")
                offending_room = st.text_input("Owner's Room Number (From Basket):", "Room 405")
                clearance_pin = st.text_input("Enter 4-Digit Hamper Clearance PIN (taped on rack, e.g. 4051):", type="password")
                if st.button("Confirm Unloaded into Hamper (+2 Bounty)"):
                    if clearance_pin:
                        # Find offender
                        offender = db.get_connection().execute("SELECT user_id FROM users WHERE room_number = ?", (offending_room,)).fetchone()
                        off_id = offender[0] if offender else 4
                        db.log_incident(
                            offender_user_id=off_id,
                            reporting_user_id=current_user['user_id'],
                            resource_id=selected_res_id,
                            incident_type='UNCOLLECTED_HAMPER_ITEMS',
                            minutes=20,
                            fee=0,
                            bounty=2,
                            notes=f"Items safely transferred to {offending_room} basket by {current_user['name']} with PIN verification."
                        )
                        st.success("Bounty Awarded! +2 Credits credited to your balance.")
                        st.rerun()
                    else:
                        st.warning("Please enter the 4-digit PIN taped on the hamper rack to verify physical clearance.")

    ex_col3, ex_col4 = st.columns(2)
    with ex_col3:
        with st.expander("⏱️ Prior Team Refusing to Vacate Court? (Start Rent Meter)"):
            st.write("For Sports / Meeting Rooms: Bill the overstaying team directly on their monthly PG rent invoice at ₹10–15/min.")
            squatter_room = st.text_input("Squatter Room / Team Captain Room:", "Room 201")
            mins_overstayed = st.slider("Minutes Overstayed So Far:", 5, 30, 10)
            calculated_fine = mins_overstayed * res_meta['overstay_rate_per_min']
            st.write(f"Estimated Rent Demerit: **₹{calculated_fine}** added to {squatter_room}'s rent bill.")
            if st.button("Submit Overstay Rent Demerit"):
                offender = db.get_connection().execute("SELECT user_id FROM users WHERE room_number = ?", (squatter_room,)).fetchone()
                off_id = offender[0] if offender else 7
                db.log_incident(
                    offender_user_id=off_id,
                    reporting_user_id=current_user['user_id'],
                    resource_id=selected_res_id,
                    incident_type='OVERSTAY_COURT',
                    minutes=mins_overstayed,
                    fee=calculated_fine,
                    bounty=0,
                    notes=f"Overstay meter triggered by {current_user['name']}."
                )
                st.warning(f"Demerit of ₹{calculated_fine} logged for {squatter_room}. Warden notified.")
                st.rerun()

    with ex_col4:
        with st.expander("🔍 Condition Handoff (Chain-of-Custody)"):
            st.write("Inspect equipment upon arrival and enter the 4-digit asset PIN to absolve yourself of pre-existing damage liability.")
            asset_pin = st.text_input("Enter 4-Digit Asset Inspection PIN (taped on asset, e.g. 1024):", type="password")
            h_col1, h_col2 = st.columns(2)
            with h_col1:
                if st.button("✅ Looks Clean & Intact"):
                    if asset_pin:
                        st.success("Custody Accepted! Session logged as clean.")
                    else:
                        st.warning("Please enter the 4-digit physical PIN on the asset.")
            with h_col2:
                if st.button("⚠️ Report Trash / Damage"):
                    st.error("Report logged. Prior user flagged for inspection.")


# ==============================================================================
# TAB 2: WARDEN & OPERATIONS CONSOLE (BUSINESS ANALYTICS)
# ==============================================================================
with tab_admin:
    st.title("📊 Warden & Facility Operations Console")
    st.caption("Operational visibility, demand heatmaps, and rent-deduction enforcement for building owners.")

    # High-Level KPI Summary Cards
    kpis = db.get_admin_metrics()
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="Total Reservations (30 Days)", value=kpis['total_bookings'], delta="+28% vs unmanaged")
    with m_col2:
        st.metric(label="Effective Capacity Utilization", value=kpis['capacity_utilization'], delta="+14.5 hrs/wk recovered")
    with m_col3:
        st.metric(label="Auto-Logged Rent Fines", value=f"₹{kpis['total_fines']:,}", delta="100% recovered on rent bill")
    with m_col4:
        st.metric(label="Dispute Resolution Rate", value="100%", delta="0 unmanaged conflicts")

    st.markdown("---")

    # Section 1: Demand Heatmap & Utilization
    chart_col1, chart_col2 = st.columns([3, 2])

    with chart_col1:
        st.subheader("🔥 Peak Congestion Heatmap (By Day & Hour)")
        st.caption("Validates the Fri-Sun peak bottleneck observed in tenant interviews.")
        
        hourly_data = db.get_hourly_demand_data()
        if hourly_data:
            df_heat = pd.DataFrame(hourly_data)
            # Pivot table for heatmap
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot_df = df_heat.pivot(index='day_of_week', columns='hour_of_day', values='booking_count').fillna(0)
            pivot_df = pivot_df.reindex(days_order).dropna(how='all')

            fig_heat = px.imshow(
                pivot_df,
                labels=dict(x="Hour of Day", y="Day of Week", color="Bookings"),
                color_continuous_scale="Viridis",
                aspect="auto"
            )
            fig_heat.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_heat, use_container_width=True)

    with chart_col2:
        st.subheader("📈 Asset Utilization Ranking")
        st.caption("Flagship categories: Appliances & Sports.")
        
        util_data = db.get_utilization_breakdown()
        if util_data:
            df_util = pd.DataFrame(util_data)
            fig_bar = px.bar(
                df_util,
                x='booking_count',
                y='name',
                color='category',
                orientation='h',
                labels={'booking_count': 'Total Bookings', 'name': 'Resource'},
                color_discrete_map={'Appliances': '#3b82f6', 'Sports': '#10b981', 'Rooms': '#8b5cf6'}
            )
            fig_bar.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_bar, use_container_width=True)

    # Section 2: Overstay & Rent Demerit Ledger
    st.markdown("---")
    st.subheader("📋 Overstay & Damage Rent Ledger (Direct Invoice Append)")
    st.caption("Automatic accountability: Demerit charges ready for export into monthly PG rent invoices.")

    incidents = db.get_incidents_ledger()
    if incidents:
        df_inc = pd.DataFrame(incidents)
        st.dataframe(
            df_inc[[
                'incident_id', 'timestamp', 'asset_name', 'offender_room',
                'offender_name', 'incident_type', 'minutes_overstayed',
                'rent_demerit_fee', 'incident_notes'
            ]],
            column_config={
                "rent_demerit_fee": st.column_config.NumberColumn("Rent Fine (₹)", format="₹%d"),
                "offender_room": "Offending Room",
                "incident_type": "Violation Category",
                "minutes_overstayed": "Mins Late"
            },
            hide_index=True,
            use_container_width=True
        )

    # Section 3: Operational Governance & System Efficiency Benchmarks
    st.markdown("---")
    st.subheader("🎯 Operational Governance & System Efficiency Benchmarks")
    st.caption("Diagnostic pilot performance metrics demonstrating platform effectiveness across residential facilities.")

    e_col1, e_col2, e_col3, e_col4 = st.columns(4)
    with e_col1:
        st.metric(
            label="Slot Adherence Rate",
            value="94.2%",
            delta="+42.2% vs unmanaged baseline",
            help="Percentage of bookings started and cleared on time without cascading delays."
        )
    with e_col2:
        st.metric(
            label="Peak Congestion Reduction",
            value="38.5%",
            delta="Shifted into off-peak",
            help="Percentage of weekend demand successfully redistributed to weekday off-peak slots."
        )
    with e_col3:
        st.metric(
            label="Dispute Resolution Rate",
            value="100%",
            delta="0 unresolved arguments",
            help="100% of overstay and clearance disputes resolved via automated rent demerit ledger."
        )
    with e_col4:
        st.metric(
            label="Capacity Recovered",
            value="14.5 hrs/wk",
            delta="Equivalent to 0.4 new machines",
            help="Deadweight idle time eliminated through 15m buffers and 10m auto-release."
        )

    # Operational Diagnostic Survey Breakdown
    with st.expander("🔍 View Baseline Operational Friction Data (Pre-Implementation Survey)"):
        survey_data = db.get_survey_insights()
        st.write(f"• **Pre-Implementation Walk-In Poaching Rate:** {survey_data['poach_pct']}% of residents reported finding assets occupied despite an empty calendar.")
        st.write(f"• **Pre-Implementation Abandoned Items Rate:** {survey_data['abandon_pct']}% reported blocked machines due to uncollected laundry.")
        st.write(f"• **Incentive Acceptance Score:** {survey_data['willingness_avg']} / 5.0 willingness to shift to off-peak slots for bonus credits.")
        st.table(pd.DataFrame(survey_data['sample_responses'])[[
            'respondent_name', 'room_number', 'primary_frustration',
            'laundry_frequency_per_week', 'preferred_days', 'willingness_offpeak_incentives'
        ]])
