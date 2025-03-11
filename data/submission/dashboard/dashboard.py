import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Memuat dataset
@st.cache_data 
def load_data():
    # Memuat dataset harian dan per jam
    daily_data = pd.read_csv("dashboard/day_df.csv")
    hourly_data = pd.read_csv("dashboard/hour_df.csv")
    
    # Mengubah kolom 'date' ke tipe datetime
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    hourly_data['date'] = pd.to_datetime(hourly_data['date'])
    
    return daily_data, hourly_data

daily_data, hourly_data = load_data()

# Fungsi untuk mengkategorikan suhu yang dirasakan
def categorize_atemp(atemp_value):
    if atemp_value < 0.3:
        return 'Dingin'
    elif 0.3 <= atemp_value < 0.6:
        return 'Sedang'
    else:
        return 'Panas'

# Menambahkan kolom baru untuk kategori suhu pada kedua dataset
daily_data['kategori_atemp'] = daily_data['atemp'].apply(categorize_atemp)
hourly_data['kategori_atemp'] = hourly_data['atemp'].apply(categorize_atemp)

# Sidebar untuk pemilihan dataset
with st.sidebar:
    st.markdown(
        """
        <style>
        .big-icon {
            font-size: 100px;  # Ukuran besar untuk ikon
            text-align: center;  # Posisi tengah
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="big-icon">🚲</div>', unsafe_allow_html=True)
    
    st.title("Pilih Dataset")
    selected_dataset = st.radio("Pilih dataset:", ("Harian", "Per Jam"))

# Memilih dataset berdasarkan pilihan pengguna
if selected_dataset == "Harian":
    data = daily_data  
else:
    data = hourly_data 

# Menentukan rentang tanggal
start_date_default = data["date"].min()
end_date_default = data["date"].max()

with st.sidebar:
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=start_date_default, max_value=end_date_default, value=[start_date_default, end_date_default]
    )

# Memfilter data berdasarkan rentang tanggal
filtered_data = data[(data["date"] >= pd.to_datetime(start_date)) & (data["date"] <= pd.to_datetime(end_date))]

# Menghitung total pengguna berdasarkan kategori suhu yang sudah difilter
temp_category_summary = filtered_data.groupby('kategori_atemp')['count'].sum().reset_index()

# Mengurutkan kategori suhu
temp_category_summary['kategori_atemp'] = pd.Categorical(temp_category_summary['kategori_atemp'], categories=['Dingin', 'Sedang', 'Panas'], ordered=True)
temp_category_summary = temp_category_summary.sort_values('kategori_atemp')

# Fungsi untuk membuat dataframe pesanan harian
def generate_daily_orders(data):
    daily_orders = data.resample(rule='D', on='date').agg({
        "count": "sum"
    })
    daily_orders = daily_orders.reset_index()
    daily_orders.rename(columns={"count": "total_users"}, inplace=True)
    return daily_orders

# Fungsi untuk membuat dataframe berdasarkan musim
def generate_seasonal_data(data):
    seasonal_data = data.groupby(by="season")["count"].sum().reset_index()
    seasonal_data.rename(columns={"count": "total_users"}, inplace=True)
    return seasonal_data

# Fungsi untuk membuat dataframe berdasarkan jam
def generate_hourly_data(data):
    if 'hour' in data.columns:
        hourly_data = data.groupby(by="hour")["count"].sum().reset_index()
        hourly_data.rename(columns={"count": "total_users"}, inplace=True)
        return hourly_data
    else:
        return pd.DataFrame()  

# Membuat dataframe untuk visualisasi
daily_orders_data = generate_daily_orders(filtered_data)
seasonal_data = generate_seasonal_data(filtered_data)
hourly_data = generate_hourly_data(filtered_data)

# Menampilkan visualisasi
st.header('Dashboard Penyewaan Sepeda 🚴‍♂️')
st.subheader('📅 Pengguna Harian')

col1, col2 = st.columns(2)
with col1:
    total_users = daily_orders_data["total_users"].sum()
    st.metric("Total Pengguna", value=total_users)

# Visualisasi pesanan harian
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_data["date"],
    daily_orders_data["total_users"],
    marker='o', 
    linewidth=2,
    color="#42A5F5" 
)
ax.set_xlabel("Tanggal", fontsize=15)
ax.set_ylabel("Total Pengguna", fontsize=15)
st.pyplot(fig)

# Visualisasi berdasarkan musim
st.subheader("🌤️ Pengguna Berdasarkan Musim")
fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    x="season",
    y="total_users",
    data=seasonal_data,
    palette=["#90CAF9", "#64B5F6", "#42A5F5", "#2196F3"], 
    ax=ax
)
ax.set_xlabel("Musim", fontsize=15)
ax.set_ylabel("Total Pengguna", fontsize=15)

# Mengatur format sumbu Y agar tidak menggunakan koma
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}'))

st.pyplot(fig)

# Visualisasi berdasarkan jam 
if selected_dataset == "Per Jam":
    st.subheader("⏰ Pengguna Berdasarkan Jam")
    if not hourly_data.empty:  
        fig, ax = plt.subplots(figsize=(16, 8))
        sns.lineplot(
            x="hour",
            y="total_users",
            data=hourly_data,
            marker='o',
            linewidth=2,
            color="#1E88E5",  
            ax=ax
        )
        ax.set_xlabel("Jam", fontsize=15)
        ax.set_ylabel("Total Pengguna", fontsize=15)
        ax.set_xticks(range(24))
        st.pyplot(fig)
    else:
        st.warning("Kolom 'hour' tidak ditemukan di dataset yang dipilih.")

# Visualisasi berdasarkan kategori suhu
st.subheader("🌡️ Pengguna Berdasarkan Kategori Suhu")
fig, ax = plt.subplots(figsize=(8, 6))
sns.barplot(
    data=temp_category_summary, 
    x='kategori_atemp', 
    y='count', 
    palette=["#64B5F6", "#42A5F5", "#1E88E5"],  
    ax=ax
)
ax.set_xlabel("Kategori Suhu yang Dirasakan", fontsize=15)
ax.set_ylabel("Total Pengguna", fontsize=15)

# Mengatur format sumbu Y agar tidak menggunakan koma
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x)}'))

st.pyplot(fig)

st.caption('Coding Camp Powered by DBS Foundation')