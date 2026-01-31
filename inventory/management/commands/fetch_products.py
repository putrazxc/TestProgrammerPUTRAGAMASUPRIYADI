from django.core.management.base import BaseCommand
import requests
import hashlib
from datetime import datetime, timedelta

from inventory.models import Produk, Kategori, Status


class Command(BaseCommand):
    help = "Fetch produk dari API Fastprint - FINAL WORKING VERSION"

    def handle(self, *args, **kwargs):
        url = "https://recruitment.fastprint.co.id/tes/api_tes_programmer"
        session = requests.Session()

        # ==================================================================
        # STEP 1: GET REQUEST - Ambil Server Date
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 1: GET Request untuk ambil server date")
        self.stdout.write("="*70)
        
        try:
            get_response = session.get(url, timeout=10)
            self.stdout.write(f"✅ GET Request berhasil (Status: {get_response.status_code})")
        except Exception as e:
            self.stderr.write(f"❌ Error saat GET request: {e}")
            return

        if "Date" not in get_response.headers:
            self.stderr.write("❌ Header 'Date' tidak ditemukan!")
            return

        # Parse server date (GMT) dan convert ke GMT+7
        server_date_str = get_response.headers["Date"]
        self.stdout.write(f"📅 Server Date (GMT): {server_date_str}")
        
        server_date_gmt = datetime.strptime(
            server_date_str,
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        # Server menggunakan GMT+7 untuk credentials (SESUAI DEBUG)
        server_date = server_date_gmt + timedelta(hours=7)
        
        self.stdout.write(f"📅 Server Date (GMT+7): {server_date.strftime('%d-%m-%Y %H:%M:%S')}")

        # Extract date components
        day = server_date.day
        month = server_date.month
        year_2digit = str(server_date.year)[2:]

        # ==================================================================
        # STEP 2: Generate Credentials
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 2: Generate credentials")
        self.stdout.write("="*70)

        # Username: tesprogrammerDDMMYYC01 (SESUAI KREDENSIAL - suffix C01)
        username = f"tesprogrammer{day:02d}{month:02d}{year_2digit}C01"

        # Password: bisacoding-DD-MM-YY (DENGAN leading zero!)
        password_raw = f"bisacoding-{day:02d}-{month:02d}-{year_2digit}"
        password_md5 = hashlib.md5(password_raw.encode()).hexdigest()

        self.stdout.write(f"\n📋 Credentials:")
        self.stdout.write(f"   Username     : {username}")
        self.stdout.write(f"   Password Raw : {password_raw}")
        self.stdout.write(f"   Password MD5 : {password_md5}")

        # ==================================================================
        # STEP 3: POST REQUEST - Login
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 3: Login ke API")
        self.stdout.write("="*70)

        payload = {
            "username": username,
            "password": password_md5
        }

        try:
            post_response = session.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            self.stdout.write(f"📡 Status: {post_response.status_code}")

            if post_response.status_code != 200:
                self.stderr.write(f"\n❌ Login gagal! Status: {post_response.status_code}")
                self.stderr.write(f"Response: {post_response.text}")
                return

        except Exception as e:
            self.stderr.write(f"❌ Error saat POST request: {e}")
            return

        # Parse JSON response
        try:
            json_data = post_response.json()
        except Exception as e:
            self.stderr.write(f"❌ Response bukan JSON: {e}")
            self.stderr.write(f"Response: {post_response.text}")
            return

        # Cek apakah ada error di response
        if json_data.get('error') == 1:
            self.stderr.write(f"❌ Error dari API: {json_data.get('ket')}")
            return

        # Cek apakah ada data
        if "data" not in json_data or not json_data["data"]:
            self.stderr.write("❌ Response tidak mengandung data produk")
            self.stderr.write(f"Response: {json_data}")
            return

        self.stdout.write(self.style.SUCCESS(f"✅ Login berhasil! Total produk: {len(json_data['data'])}"))

        # ==================================================================
        # STEP 4: Simpan ke Database
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 4: Menyimpan data ke database")
        self.stdout.write("="*70)

        total_created = 0
        total_updated = 0
        errors = []

        # Buat counter untuk auto-generate ID jika tidak ada
        kategori_id_counter = 1
        status_id_counter = 1
        kategori_map = {}  # untuk mapping nama kategori ke ID
        status_map = {}    # untuk mapping nama status ke ID

        for item in json_data["data"]:
            try:


                # Ambil atau buat kategori berdasarkan NAMA
                kategori_nama = item.get("kategori", "Unknown")
                
                # Jika kategori belum pernah ditemui, assign ID baru
                if kategori_nama not in kategori_map:
                    kategori, created = Kategori.objects.get_or_create(
                        nama_kategori=kategori_nama,
                        defaults={"id_kategori": kategori_id_counter}
                    )
                    if created:
                        kategori_map[kategori_nama] = kategori_id_counter
                        kategori_id_counter += 1
                    else:
                        kategori_map[kategori_nama] = kategori.id_kategori
                else:
                    kategori = Kategori.objects.get(nama_kategori=kategori_nama)

                # Ambil atau buat status berdasarkan NAMA
                status_nama = item.get("status", "Unknown")
                
                # Jika status belum pernah ditemui, assign ID baru
                if status_nama not in status_map:
                    status, created = Status.objects.get_or_create(
                        nama_status=status_nama,
                        defaults={"id_status": status_id_counter}
                    )
                    if created:
                        status_map[status_nama] = status_id_counter
                        status_id_counter += 1
                    else:
                        status_map[status_nama] = status.id_status
                else:
                    status = Status.objects.get(nama_status=status_nama)

                # Simpan/update produk
                produk, created = Produk.objects.update_or_create(
                    id_produk=item.get("id_produk"),
                    defaults={
                        "nama_produk": item.get("nama_produk", ""),
                        "harga": item.get("harga", 0),
                        "kategori": kategori,
                        "status": status
                    }
                )

                if created:
                    total_created += 1
                    self.stdout.write(f"  ✅ Created: {item.get('nama_produk', 'N/A')}")
                else:
                    total_updated += 1
                    self.stdout.write(f"  🔄 Updated: {item.get('nama_produk', 'N/A')}")

            except Exception as e:
                error_msg = f"Error pada produk '{item.get('nama_produk', 'N/A')}': {e}"
                errors.append(error_msg)
                self.stderr.write(f"  ❌ {error_msg}")

        # Display summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("✅ PROSES SELESAI!"))
        self.stdout.write("="*70)
        self.stdout.write(f"📦 Produk dibuat baru : {total_created}")
        self.stdout.write(f"🔄 Produk diupdate    : {total_updated}")
        self.stdout.write(f"📊 Total              : {total_created + total_updated}")
        
        if errors:
            self.stdout.write(f"⚠️  Error             : {len(errors)}")
        else:
            self.stdout.write(f"✨ Tidak ada error!")
        
        # Tampilkan summary kategori dan status
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📋 Summary Kategori dan Status")
        self.stdout.write("="*70)
        self.stdout.write(f"Total Kategori : {Kategori.objects.count()}")
        self.stdout.write(f"Total Status   : {Status.objects.count()}")
        
        self.stdout.write("\nKategori yang tersimpan:")
        for kat in Kategori.objects.all():
            self.stdout.write(f"  • {kat.nama_kategori} (ID: {kat.id_kategori})")
        
        self.stdout.write("\nStatus yang tersimpan:")
        for st in Status.objects.all():
            self.stdout.write(f"  • {st.nama_status} (ID: {st.id_status})")
        
        self.stdout.write("")