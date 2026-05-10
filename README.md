# Kikoa - Gestion d'Événements Privés

Kikoa est une application web simple et légère construite avec Django pour gérer des événements, des invitations et des participants.

## 🚀 Déploiement en Production (VPS + SQLite)

Ce guide explique comment déployer Kikoa sur un VPS (Ubuntu/Debian) pour un usage privé.

### 1. Pré-requis sur le VPS

Mettez à jour le système et installez les dépendances nécessaires :

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y
```

### 2. Installation de l'application

Placez-vous dans `/var/www` et clonez votre projet :

```bash
cd /var/www
# Remplacez par votre repo ou transférez vos fichiers via SCP/SFTP
git clone https://github.com/votre-compte/Kikoa.git
cd Kikoa

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances
pip install django djangorestframework gunicorn
```

### 3. Configuration de Django

Éditez le fichier `Kikoa/settings.py` :

*   `DEBUG = False`
*   `ALLOWED_HOSTS = ['votre_ip_vps', 'votre_domaine.com']`
*   Configurez le dossier statique : `STATIC_ROOT = BASE_DIR / "staticfiles"`

Préparez la base de données et les fichiers :

```bash
python manage.py collectstatic --noinput
python manage.py migrate
```

### 4. Configuration de Gunicorn

Créez un service systemd pour Gunicorn : `sudo nano /etc/systemd/system/kikoa.service`

```ini
[Unit]
Description=Gunicorn instance for Kikoa
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/Kikoa
ExecStart=/var/www/Kikoa/venv/bin/gunicorn --workers 3 --bind unix:/var/www/Kikoa/kikoa.sock Kikoa.wsgi:application

[Install]
WantedBy=multi-user.target
```

Activez le service :
```bash
sudo systemctl start kikoa
sudo systemctl enable kikoa
```

### 5. Configuration de Nginx (Proxy Inverse)

Créez le fichier de configuration : `sudo nano /etc/nginx/sites-available/kikoa`

```nginx
server {
    listen 80;
    server_name votre_ip_vps votre_domaine.com;

    location /static/ {
        alias /var/www/Kikoa/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/Kikoa/kikoa.sock;
    }
}
```

Activez le site et redémarrez Nginx :
```bash
sudo ln -s /etc/nginx/sites-available/kikoa /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Permissions SQLite (Crucial)

Pour que SQLite fonctionne, l'utilisateur `www-data` doit pouvoir écrire dans le fichier de base de données **et** dans le dossier parent :

```bash
sudo chown www-data:www-data /var/www/Kikoa/db.sqlite3
sudo chown www-data:www-data /var/www/Kikoa
```

---

## 🛠 Maintenance & Commandes Utiles

*   **Redémarrer l'app** : `sudo systemctl restart kikoa`
*   **Voir les logs d'erreur** : `sudo journalctl -u kikoa`
*   **Logs Nginx** : `sudo tail -f /var/log/nginx/error.log`
*   **Créer un superutilisateur** (une fois en ligne) :
    ```bash
    cd /var/www/Kikoa
    source venv/bin/activate
    python manage.py createsuperuser
    ```

---

## 🔒 Sécurité (Optionnel mais recommandé)

Installez un certificat SSL gratuit avec Certbot :
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d votre_domaine.com
```
