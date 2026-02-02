"""
Django Management Command: Fetch Produk dari API Fastprint
Version: SMART - dengan multiple strategi berdasarkan hint

HINT dari soal: CEK RESPONSE, HEADER, COOKIES
"""

from django.core.management.base import BaseCommand
import requests
import hashlib
from datetime import datetime, timedelta

from inventory.models import Produk, Kategori, Status


class Command(BaseCommand):
    help = "Fetch produk dari API Fastprint - SMART VERSION"

    def handle(self, *args, **kwargs):
        url = "https://recruitment.fastprint.co.id/tes/api_tes_programmer"
        session = requests.Session()

        # ==================================================================
        # STEP 1: GET REQUEST - Ambil Server Date & Analisis Header/Cookies
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 1: GET Request - Analisis Header, Cookies & Response")
        self.stdout.write("="*70)
        
        try:
            get_response = session.get(url, timeout=10)
            self.stdout.write(f"✅ GET Request berhasil (Status: {get_response.status_code})")
        except Exception as e:
            self.stderr.write(f"❌ Error saat GET request: {e}")
            return

        # Tampilkan SEMUA header (sesuai hint)
        self.stdout.write("\n📋 Response Headers:")
        suffix_from_header = None
        
        for key, value in get_response.headers.items():
            self.stdout.write(f"   {key}: {value}")
            
            # Cari kemungkinan suffix di header
            key_lower = key.lower()
            if any(keyword in key_lower for keyword in ['suffix', 'code', 'auth', 'token', 'fastprint']):
                self.stdout.write(f"   ⚠️  POSSIBLE HINT: {key} = {value}")
                if 'suffix' in key_lower:
                    suffix_from_header = value

        # Tampilkan SEMUA cookies (sesuai hint)
        self.stdout.write("\n🍪 Cookies:")
        suffix_from_cookie = None
        
        if get_response.cookies:
            for cookie in get_response.cookies:
                self.stdout.write(f"   {cookie.name}: {cookie.value}")
                cookie_lower = cookie.name.lower()
                if any(keyword in cookie_lower for keyword in ['suffix', 'code', 'auth', 'token']):
                    self.stdout.write(f"   ⚠️  POSSIBLE HINT: {cookie.name} = {cookie.value}")
                    if 'suffix' in cookie_lower:
                        suffix_from_cookie = cookie.value
        else:
            self.stdout.write("   (tidak ada cookies)")

        # Cek response body (sesuai hint)
        self.stdout.write("\n📄 Response Body:")
        try:
            if get_response.text:
                self.stdout.write(f"   Length: {len(get_response.text)} bytes")
                
                try:
                    json_data = get_response.json()
                    self.stdout.write("   Format: JSON")
                    
                    # Cari hint di JSON
                    import json
                    json_str = json.dumps(json_data)
                    if 'suffix' in json_str.lower():
                        self.stdout.write("   ⚠️  Keyword 'suffix' ditemukan di response JSON!")
                        self.stdout.write(f"   Content: {json_str[:200]}")
                        
                except:
                    self.stdout.write("   Format: Text/HTML")
                    if 'suffix' in get_response.text.lower():
                        self.stdout.write("   ⚠️  Keyword 'suffix' ditemukan di response text!")
        except Exception as e:
            self.stdout.write(f"   Error: {e}")

        # Parse server date
        if "Date" not in get_response.headers:
            self.stderr.write("❌ Header 'Date' tidak ditemukan!")
            return

        server_date_str = get_response.headers["Date"]
        self.stdout.write(f"\n📅 Server Date (GMT): {server_date_str}")
        
        server_date_gmt = datetime.strptime(
            server_date_str,
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        # GMT-1 (sesuai debug yang berhasil)
        server_date = server_date_gmt - timedelta(hours=1)
        
        self.stdout.write(f"📅 Server Date (GMT-1): {server_date.strftime('%d-%m-%Y %H:%M:%S')}")

        # Extract date components
        day = server_date.day
        month = server_date.month
        year_2digit = str(server_date.year)[2:]

        # Hitung berbagai kemungkinan suffix
        day_of_year = server_date.timetuple().tm_yday
        week_of_year = server_date.isocalendar()[1]

        # ==================================================================
        # STEP 2: Generate Multiple Possible Credentials
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 2: Generate credentials dengan multiple strategi")
        self.stdout.write("="*70)

        # Password (fixed format)
        password_raw = f"bisacoding-{day:02d}-{month:02d}-{year_2digit}"
        password_md5 = hashlib.md5(password_raw.encode()).hexdigest()

        self.stdout.write(f"\n🔐 Password:")
        self.stdout.write(f"   Raw: {password_raw}")
        self.stdout.write(f"   MD5: {password_md5}")

        # Generate possible suffixes (berdasarkan analisis)
        possible_suffixes = []
        
        # 1. Dari header/cookie (prioritas tertinggi)
        if suffix_from_header:
            possible_suffixes.append(("Header", suffix_from_header))
        if suffix_from_cookie:
            possible_suffixes.append(("Cookie", suffix_from_cookie))
        
        # 2. Berdasarkan kalkulasi tanggal
        possible_suffixes.extend([
            ("Day of Year", f"C{day_of_year:02d}"),
            ("Week of Year", f"C{week_of_year:02d}"),
            ("Day + 20", f"C{day + 20:02d}"),  # Pattern dari C22 = 2+20
            ("Day + Month", f"C{day + month:02d}"),
            ("Day itself", f"C{day:02d}"),
            ("Fallback C22", "C22"),  # Dari debug yang berhasil
        ])

        self.stdout.write(f"\n🎯 Akan mencoba {len(possible_suffixes)} strategi suffix:")
        for idx, (strategy, suffix) in enumerate(possible_suffixes, 1):
            self.stdout.write(f"   {idx}. {strategy}: {suffix}")

        # ==================================================================
        # STEP 3: POST REQUEST - Login dengan Multiple Attempts
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 3: Mencoba Login ke API")
        self.stdout.write("="*70)

        json_data = None
        successful_username = None

        for idx, (strategy, suffix) in enumerate(possible_suffixes, 1):
            username = f"tesprogrammer{day:02d}{month:02d}{year_2digit}{suffix}"
            
            self.stdout.write(f"\n[Attempt {idx}/{len(possible_suffixes)}] Strategi: {strategy}")
            self.stdout.write(f"   Username: {username}")

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
                
                self.stdout.write(f"   Status: {post_response.status_code}")

                if post_response.status_code == 200:
                    try:
                        json_data = post_response.json()
                        
                        # Cek apakah benar-benar sukses
                        if json_data.get('error') == 0 or ('data' in json_data and json_data['data']):
                            successful_username = username
                            self.stdout.write(self.style.SUCCESS(f"\n   ✅ BERHASIL dengan strategi: {strategy}!"))
                            break
                        else:
                            self.stdout.write(f"   Error: {json_data.get('ket', 'Unknown')}")
                    except Exception as e:
                        self.stdout.write(f"   JSON Parse Error: {e}")
                else:
                    try:
                        error_data = post_response.json()
                        self.stdout.write(f"   Error: {error_data.get('ket', 'Unknown')}")
                    except:
                        self.stdout.write(f"   Error: HTTP {post_response.status_code}")

            except Exception as e:
                self.stdout.write(f"   Exception: {e}")
                continue

        # Jika semua gagal
        if not json_data or not successful_username:
            self.stderr.write("\n❌ Semua strategi login gagal!")
            self.stderr.write("\n💡 Troubleshooting:")
            self.stderr.write("1. Periksa header & cookies di output di atas")
            self.stderr.write("2. Mungkin ada custom header yang berisi suffix")
            self.stderr.write("3. Hubungi recruiter untuk konfirmasi format terbaru")
            return

        # Cek apakah ada data
        if "data" not in json_data or not json_data["data"]:
            self.stderr.write("❌ Response tidak mengandung data produk")
            self.stderr.write(f"Response: {json_data}")
            return

        self.stdout.write("\n" + "🎉"*35)
        self.stdout.write(self.style.SUCCESS("✅ ✅ ✅ LOGIN BERHASIL! ✅ ✅ ✅"))
        self.stdout.write("🎉"*35)
        self.stdout.write(f"\n📦 Total Produk: {len(json_data['data'])}")
        self.stdout.write(f"👤 Username yang berhasil: {successful_username}")

        # ==================================================================
        # STEP 4: Simpan ke Database
        # ==================================================================
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STEP 4: Menyimpan data ke database")
        self.stdout.write("="*70)

        total_created = 0
        total_updated = 0
        errors = []

        for item in json_data["data"]:
            try:
                # Ambil atau buat kategori
                kategori_nama = item.get("kategori", "Unknown")
                kategori, _ = Kategori.objects.get_or_create(
                    nama_kategori=kategori_nama
                )

                # Ambil atau buat status
                status_nama = item.get("status", "Unknown")
                status, _ = Status.objects.get_or_create(
                    nama_status=status_nama
                )

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