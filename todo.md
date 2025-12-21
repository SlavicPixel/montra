# Montra – TODO (Faza 1)

## 0. Osnovna struktura projekta
- [x] Provjeriti strukturu Django appova
  - [x] `users` 
  - [x] `transactions` ili `expenses` (rashodi, kategorije)
- [x] Podesiti PostgreSQL konekciju (settings.py)
- [x] Provjeriti da migracije prolaze bez grešaka

---

## 1. Autentikacija i korisnici
- [x] Implementirati user registraciju
- [x] Implementirati login view
- [x] Implementirati logout view
- [ ] Zaštititi sve expense view-e s `login_required`
- [ ] Ograničiti pristup podacima isključivo na `request.user`

---

## 2. Modeli (finalna provjera) 
Ovdje treba popraviti models.py da radi bolje trenutno je samo osnovno 
- [x] `Expense` model
  - [x] naziv (npr. "Konzum")
  - [x] iznos (DecimalField, uvijek > 0)
  - [x] kategorija (ForeignKey)
  - [x] opis (optional)
  - [x] datum
  - [x] korisnik (ForeignKey -> User)
- [x] `Category` model
  - [x] naziv (unique)

---

## 3. Predefinirane kategorije - automatski se iz dataseta uzimaju

- [x] Kreirati početne kategorije:
  - [x] Hrana i piće
  - [x] Transport
  - [x] Računi
  - [x] Shopping

---

## 4. Import podataka 
- [ ] Provjeriti da CSV import koristi ispravan `User`
- [ ] Validirati iznose (pozitivni brojevi)
- [ ] Validirati datume
- [ ] Mapirati kategorije iz CSV-a na postojeće `Category` zapise
- [ ] Osigurati da import ne duplicira podatke

---

## 5. CRUD funkcionalnosti za rashode
- [ ] List view (samo userovi rashodi)
- [ ] Create view (unos rashoda)
- [ ] Update view
- [ ] Delete view
- [ ] Osigurati da user ne može editati / brisati tuđe rashode

---

## 6. Filtriranje i sortiranje
- [ ] Filtriranje po datumu (od / do)
- [ ] Filtriranje po kategoriji
- [ ] Sortiranje po datumu (desc default)
- [ ] Sortiranje po iznosu (optional)

---

## 7. Osnovni dashboard (expenses only)
- [ ] Ukupna potrošnja (SUM svih rashoda)
- [ ] Potrošnja po kategorijama
- [ ] Ukupna potrošnja za odabrani period (npr. mjesec)
- [ ] Prikaz podataka za trenutno prijavljenog korisnika

---

## 8. Templatei (minimalni UI)
- [ ] Base template
- [ ] Lista rashoda (tablica)
- [ ] Forma za dodavanje / uređivanje rashoda
- [ ] Gumbi za edit / delete
- [ ] Navigacija (Dashboard / Rashodi / Logout)

---

## 9. Validacija i UX
- [ ] Validacija iznosa (mora biti > 0)
- [ ] Prikaz poruka o uspjehu / greškama (Django messages)
- [ ] Potvrda prije brisanja rashoda

---

## 10. Docker (minimalno za fazu 1)
- [ ] Dockerfile za Django
- [ ] docker-compose.yml
  - [ ] Django service
  - [ ] PostgreSQL service
- [ ] `docker-compose up` pokreće aplikaciju bez grešaka

---

## 11. Dokumentacija
- [ ] Kratki README (kako pokrenuti projekt)
- [ ] Opis funkcionalnosti 1. faze
- [ ] Popis tehnologija

---

## 12. Finalna provjera
- [ ] Svaki korisnik vidi samo svoje rashode
- [ ] CRUD radi bez grešaka
- [ ] Import podataka ispravno radi
- [ ] Projekt se pokreće lokalno i u Dockeru
