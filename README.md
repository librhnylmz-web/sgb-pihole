# SGB → Pi-hole Domain Blocklist

T.C. Siber Güvenlik Başkanlığı'nın herkese açık API'sindeki **domain** kayıtlarını, Pi-hole uyumlu `domains.txt` dosyasına dönüştürür. Resmî proje değildir.

**Kaynak:** https://siberguvenlik.gov.tr/api/

## Kullanım

1. Bu içeriği GitHub'da **public** bir repo'ya yükleyin.
2. Repo → **Actions** → **Update SGB Pi-hole list** → **Run workflow**.
3. İlk başarılı çalışmadan sonra `domains.txt` oluşur.
4. Pi-hole → **Lists/Adlists** bölümüne aşağıdaki URL'yi ekleyin:

```
https://raw.githubusercontent.com/USERNAME/REPO/main/domains.txt
```

5. Pi-hole'da **Update Gravity** çalıştırın. Pi-hole kendi Gravity güncelleme zamanlamasına göre sonraki değişiklikleri alır.

## Otomasyon

GitHub Actions her gün **02:17 UTC** (Türkiye saati 05:17) çalışır ve API'nin tüm `domain` sayfalarını çeker. Tekilleştirme ve format doğrulama yapar. Sadece farklı bir liste oluştuğunda commit atar. API başarısız olursa eski listeyi korur. Actions zamanlamaları yoğunluk nedeniyle gecikebilir.

**Elle çalıştırmak için:** `python3 scripts/update.py` (yalnızca Python standart kütüphanesi).

## Dikkat

- Yalnızca `type=domain` alınır. URL'lerden domain çıkartılmaz; IP adresleri Pi-hole alan adı listesine alınmaz.
- Alt alan adları korunur; `x.example.com`, otomatik olarak `example.com`'a genişletilmez.
- Kaynakta eski veya artık temizlenmiş alan adları olabilir. Pi-hole'un izin listesi (allowlist) yanlış pozitifler için kullanılabilir.
- Başka kullanıcıların listeyi kullanmasından önce API veri paylaşım şartlarını gözden geçirin.
- Liste 400 bin+ satır olabileceği için Pi-hole cihazınızın bellek/Gravity kapasitesine dikkat edin.
- Mevcut git dalınız `main` değilse raw URL'deki dal adını değiştirin.
