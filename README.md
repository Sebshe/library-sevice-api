# Library Service API

## Project Description

The library management system will address the following issues in the current manual system:

- Lack of book inventory tracking
- Inability to check availability of specific books
- Cash-only payments without credit card support
- Manual tracking of book returns and late returns

## Features

* JWT authenticated.
* Admin panel /admin/
* Documentation at /api/doc/swagger/
* Books inventory management.
* Books borrowing management.
* Notifications service through Telegram API (bot and chat).
* Scheduled notifications with Django Q and Redis.
* Payments handle with Stripe API.

## Getting access

* create user via /user/
* get access token via /user/token/

## How to run with Docker

Docker should be installed.

Create `.env` file with your variables.

```shell
docker-compose build
docker-compose up
```
