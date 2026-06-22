# Crypto Big Data Pipeline & Analytics Dashboard 🚀

## 📋 Présentation du Projet
Ce projet a été réalisé dans le cadre de mon projet final ("Fil Rouge") de fin d'études. Il consiste en la mise en place d'un pipeline de données de bout en bout automatisation de l'ingestion, de la transformation et de la visualisation des données du marché des cryptomonnaies. 

L'objectif est d'offrir une plateforme décisionnelle moderne permettant de suivre la santé du marché global et d'analyser en détail les performances de chaque actif.

---

## 🏗️ Architecture Technique (End-to-End)

Le pipeline repose sur une architecture moderne de type **Modern Data Stack** :
1. **Ingestion (Raw Data) :** Extraction automatisée des données du marché de l'API **CoinGecko**.
2. **Orchestration :** Flux planifiés et gérés entièrement via **Apache Airflow** dans un environnement **Dockerized**.
3. **Stockage & Data Warehousing :** Architecture médaillon implémentée sur **MinIO** et **Snowflake** :
   * 🥉 **Bronze Layer :** Stockage des fichiers bruts JSON/CSV.
   * 🥈 **Silver Layer :** Nettoyage, typage et structuration des données historiques.
   * 🥇 **Gold Layer :** Modélisation dimensionnelle (Tables de faits `FACT_CRYPTO_METRICS` et dimensions `DIM_CRYPTO`) optimisée pour l'analyse.
4. **Restitution BI :** Création de tableaux de bord interactifs connectés en direct sur **Tableau**.

---

## 📊 Solution Business Intelligence (Tableau)

L'environnement analytique est divisé en deux tableaux de bord interconnectés pour allier vision macro et micro :

### 1. Main Dashboard (Vue Comparative)
Une vue d'ensemble macro-économique conçue pour identifier les tendances du marché global :
* **KPI Globaux :** Suivi instantané du volume total et de la capitalisation globale du marché (exprimés en Milliards/Billions `B`/`T`).
* **Line Chart Temporel :** Analyse de l'évolution dynamique des prix.
* **Top 10 Volume (Bar Chart) :** Identification des actifs les plus liquides du moment.
* **Scatter Plot (Analyse de Corrélation) :** Mise en relation du volume d'échange et de la variation de prix sur 24 heures (`Pct Change 24H`).

### 2. Detailed Dashboard (Zoom Analytique)
Une vue granulaire activée dynamiquement par l'utilisateur :
* **Fiche Crypto Dynamique :** Affichage en temps réel du prix, de la variation sur 24h et d'indicateurs de tendance contextuels colorés (▲ Vert / ▼ Rouge).
* **Heatmap :** Matrice de performance visuelle mettant en évidence l'évolution quotidienne des actifs.
* **Detailed View (Feuille 6) :** Table de données brute et propre, structurée jour par jour pour un audit approfondi.
* **Action d'Interactivité :** Un clic sur un actif du *Main Dashboard* applique un filtre croisé automatique et redirige l'utilisateur vers ce *Detailed Dashboard*.

---

## 🚀 Comment exécuter le projet

### Flux d'intégration (Backend)
1. Lancer l'environnement Docker :
```bash
   docker-compose up -d
