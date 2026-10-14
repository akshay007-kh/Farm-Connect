# FarmConnect: staged build plan

FarmConnect is a Django marketplace for farmers and customers, with expert support and data-backed agricultural services. This starter is a runnable MVP foundation: authentication, crop listings/search, cart, transactional checkout, stock updates, consultation/community models, and seller analytics. ML, messaging, weather and payment integrations are staged separately.

## Architecture

```text
Browser (Django templates; later mobile client)
  | HTTPS/session authentication
Django: accounts, marketplace, advisory, services
  | ORM/transactions                  | service adapters
MySQL 8+ (SQLite local fallback)       | Open-Meteo, email/SMS, ML models
```

Keep business operations in service modules, views thin, and external API/model calls behind adapters. Production needs HTTPS, persistent media storage, scheduled jobs, monitoring, backups, and policy/security review.

## Set up (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Browse `/` for the public home page. Staff can use the in-project admin sign-in at `/accounts/admin-login/` and dashboard at `/control/`; admins manage listings and order status there. The community login at `/accounts/login/` sends each role to its own dashboard. Farmer and customer signups are available from the home page. Farmers can add/edit crop listings with JPG/PNG/WebP product photos up to 5 MB; photos are stored under `media/crop_listings/` and served locally while `DEBUG=True`. Configure persistent object storage/CDN for production. Customers choose quantity on each crop, edit/remove cart items, enter delivery name/phone/address/city/district/PIN at checkout, and get an order record with a delivery-address snapshot. Their latest delivery details are saved to their profile to prefill the next checkout. Django's built-in system console remains tucked at `/system-admin/` for maintenance only. SQLite is the zero-configuration local default. For MySQL, create a database, install `requirements-mysql.txt`, then set `DB_ENGINE=django.db.backends.mysql` and `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` in `.env` before migration.

## Environment and keys

`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`; MySQL variables above. No third-party key is needed for the MVP. Open-Meteo forecast access does not require a key for non-commercial use; review current terms/rate limits before launch. Email/SMS, payment, and LLM chatbot providers each require their own credentials and are not wired into the starter. Never commit `.env`.

## Models

- `accounts.User`: customer/farmer/expert role, contact and district; Django staff/superuser is the separate admin authority.
- `marketplace.CropListing`: owner, crop/variety, price/kg, stock/kg, district, visibility.
- `CartItem`, `Order`, `OrderItem`: customer cart and order snapshots (name and unit price retained); checkout locks listings and decrements stock within one database transaction.
- `advisory.Consultation`, `CommunityQuestion`, `CommunityReply`: consultation lifecycle and moderated community content.
- `services.Notification`: in-app notification record.

## Implementation stages

1. **MVP in this folder:** Django setup, public home page, signup/login/logout, role-based redirects, custom staff dashboard, searchable marketplace, farmer-managed listings, cart, checkout, inventory, order history, seller/customer summaries.
2. **Seller experience:** self-service listing forms, farmer verification, listing images, order acceptance/cancellation/refunds, low-stock alerts.
3. **Expert/community:** appointment availability, expert-only responses, question/reply pages, reporting/moderation, reminders.
4. **ML services:** data ingestion, cleaning, baseline vs model comparison, versioning, confidence/uncertainty, local validation and human escalation.
5. **Integrations:** weather cards and scheduled alerts, email/SMS, Malayalam chatbot grounded in approved content, optional payments.
6. **Production:** MySQL, object storage, HTTPS, backups, monitoring, permissions, privacy/retention rules and accessibility.

## Datasets and model design

- [India OGD daily mandi prices](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi): best starting point for India-local price history. Check API/catalog access and terms; normalize commodity, market, variety, date, and units.
- [FAOSTAT](https://www.fao.org/faostat/en/#data): long-run country/commodity production, yield and producer-price context; national data is not local mandi history.
- [PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset): leaf-image prototype data. Controlled backgrounds create a field domain gap; confirm license and test with locally collected field images.
- [Open-Meteo forecast API](https://open-meteo.com/en/docs): weather displays/alerts using coordinates; cache calls and confirm current commercial terms.
- Crop-recommendation CSVs from Kaggle are convenient teaching data but may be small or curated. Verify provenance/license; gather local soil, season and outcome data before making real agronomic claims.

### Crop recommendation (Scikit-learn)

Features: nitrogen, phosphorus, potassium, pH, rainfall, temperature, humidity, season and region where available. Begin with `Pipeline(SimpleImputer, RandomForestClassifier)`, stratified metrics (macro-F1/confusion matrix), and a grouped/local holdout. Benchmark output is educational, not calibrated advice.

### Crop price prediction (Scikit-learn)

Use cleaned mandi time series. Compare seasonal-naive baseline to `HistGradientBoostingRegressor`; create lag/rolling/calendar features using past observations only. Split chronologically, report MAE by crop/market and uncertainty; refuse predictions with too little history.

### Disease detection

PlantVillage can prototype a classifier, but its studio-like images differ from field photos. For raw images, use transfer learning with PyTorch/TensorFlow; Scikit-learn is not the right image backbone. Evaluate per-class recall and field-set results. Show confidence and route uncertain images to an expert.

The starter includes `services/chatbot.py`, a Malayalam FAQ fallback with expert escalation. It is intentionally deterministic; a production chatbot should retrieve from reviewed Malayalam agricultural sources and preserve the escalation path. The `services/weather.py` adapter provides a forecast call; schedule/cache calls and save user consent/location preferences before building alerts. Notification records are modeled, while delivery channels belong in a later provider integration.

To train the example crop model after installing requirements, prepare the CSV columns shown in `ml/train_crop_recommender.py` and run `python ml/train_crop_recommender.py path/to/crop_data.csv`. It prints a holdout report and saves a joblib artifact; load it through `ml/crop_recommendation.py`. The price example accepts one normalized market/commodity CSV with `date,price`: `python ml/train_price_forecaster.py path/to/market_prices.csv`. It uses a chronological holdout and lag features. Compare against a seasonal-naive baseline and validate data sufficiency before exposing either model to users. Both examples need real data and domain review.

## Routes and limitations

`/` public home and marketplace; `/accounts/signup/`, `/accounts/login/`, `/accounts/admin-login/`, `/accounts/logout/`; `/customer/`, `/dashboard/` (farmer), `/expert/`, `/control/` (staff admin); `/farmer/listings/new/`, `/cart/`, `/checkout/`, `/orders/`. Cart quantity updates and item removal are POST-only. Run `python manage.py migrate` after updating to apply delivery-profile and order-address migrations. `/system-admin/` is Django's maintenance console and is not part of the normal user journey.

This is a local/course MVP, not a public commerce deployment. Add role checks and self-service forms before opening farmer operations; image validation, payment reconciliation, cancellation/refund rules, abuse controls, secure cookies and HTTPS before production. Do not present ML outputs as guaranteed diagnosis, treatment or price.
