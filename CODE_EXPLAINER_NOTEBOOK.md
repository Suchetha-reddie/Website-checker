# 🧸 The Super Simple Code Guide: How This Project Works

> **Goal of this guide:** Explain every piece of code in this project so simply that anyone—even if it's your very first day learning to code—can understand exactly what is happening.

---

## 🌟 The 10-Second Summary

Imagine this project is a **Security Inspector** for websites:

```
               ┌──────────────────────────────────────┐
               │  1. You type: "google.com"           │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │  2. Python runs 10 quick checks:     │
               │     • Is it alive?                   │
               │     • Does it have an ID badge?      │
               │     • Are doors locked?              │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │  3. Gives a Score: "85/100 (Grade A)"│
               │  4. Lets you download an Excel sheet │
               └──────────────────────────────────────┘
```

That's the entire app! Now, let's see how the code actually does each step.

---

## 🚦 The 10 Steps Explained Like You're 10 Years Old

---

### Step 1: Cleaning Messy URLs (`modules/url_validator.py`)

* **The Problem:** People type URLs in messy ways. Some type `google.com`, some type `http://GOOGLE.COM/`, and some type weird things like `javascript:...`.
* **What the code does:** It acts like an address cleaner.
* **The Code in Simple Terms:**
  ```python
  # If someone forgot the "https://", add it for them!
  if not url.startswith("http"):
      url = "https://" + url
  ```
* **Result:** No matter how messy the user's input is, the rest of the code always gets a neat, clean URL like `https://google.com/`.

---

### Step 2: The "Don't Hack Yourself" Shield (`modules/url_validator.py`)

* **The Problem (SSRF):** What if a sneaky user tells our scanner to scan `127.0.0.1`? `127.0.0.1` means **"this computer itself"**! If the scanner scanned itself, someone could spy on our own computer's private files.
* **What the code does:** It looks up the IP number of the website. If the number belongs to our own computer or our private home Wi-Fi, it shouts: **"STOP! Blocked!"**
* **The Code in Simple Terms:**
  ```python
  ip = socket.gethostbyname(hostname)

  # Is this IP trying to talk to our own computer?
  if ip.startswith("127.") or ip.startswith("192.168."):
      return "Blocked! You cannot scan private internal computers."
  ```

---

### Step 3: The Doorbell Test (`modules/availability_checker.py`)

* **The Problem:** We need to know: Is the website awake, and how fast is it?
* **What the code does:** It rings the website's doorbell with a stopwatch.
* **The Code in Simple Terms:**
  ```python
  start_time = time.time()          # Start the stopwatch
  response = requests.get(url)      # Ring the doorbell
  how_long = time.time() - start_time # Stop the stopwatch

  milliseconds = round(how_long * 1000)

  if milliseconds < 500:
      speed = "Fast 🟢"
  else:
      speed = "Slow 🔴"
  ```
* **Clever Trick in the Code:** We use `stream=True`. That tells Python: *"Just check if the front door opened—don't download all the heavy pictures and videos inside."* This makes our scan super fast!

---

### Step 4: Finding the Street Address (`modules/ip_resolver.py`)

* **The Problem:** Computers don't know what words like `youtube.com` mean. They only understand number addresses like `142.250.190.46`.
* **What the code does:** It looks up both the old style address (IPv4) and the new style address (IPv6).
* **The Code in Simple Terms:**
  ```python
  # Ask the computer's network card for all IP addresses of the website
  addresses = socket.getaddrinfo("youtube.com", None)
  ```

---

### Step 5: Reading the Phonebook (`modules/dns_checker.py`)

* **The Problem:** Every domain has a "phonebook" called DNS. It lists who delivers their email, who hosts their servers, and verification notes.
* **What the code does:** It asks the phonebook for 6 specific pages:
  1. **A**: The computer's IPv4 address.
  2. **AAAA**: The computer's IPv6 address.
  3. **MX**: The mail carrier (e.g. Gmail or Outlook).
  4. **NS**: The company managing the phonebook (e.g. Cloudflare).
  5. **TXT**: Anti-spam notes proving nobody is faking emails from this domain.
  6. **SOA**: Who owns the phonebook.

---

### Step 6: Checking the Digital Passport (`modules/ssl_checker.py`)

* **The Problem:** When you visit a bank, how do you know you're talking to the real bank and not an imposter? That's what an **SSL Certificate** is for. It is the website's official digital passport.
* **What the code does:** It inspects the passport:
  1. **Is it real?** (Signed by an official government-like authority like Google or DigiCert).
  2. **Did it expire?** Certificates only last for a year. If it expired, visitors get a big red scary warning screen!
  3. **Does the name match?** If the passport says `fake.com` but you visited `bank.com`, that's an alert!
* **The Code in Simple Terms:**
  ```python
  # Connect to the website securely
  conn = ssl_context.wrap_socket(socket.socket(), server_hostname="bank.com")
  conn.connect(("bank.com", 443))

  passport = conn.getpeercert() # Get the digital certificate!

  # Check when it expires
  expiry_date = passport['notAfter']
  days_left = expiry_date - today

  if days_left < 0:
      print("Certificate is expired! ❌")
  ```

---

### Step 7: HTTP & Cookies Check (`modules/http_checker.py`)

* **The Problem:** 
  1. What happens if a user types insecure `http://` instead of `https://`? Does the website automatically push them to safety?
  2. When you log in, websites give you a small badge called a **Cookie**. If someone steals that badge, they can log into your account!
* **What the code does:**
  - It checks if `http://` redirects to `https://`.
  - It checks if cookies have two safety locks:
    - **`Secure` lock**: *"Only send this cookie over encrypted HTTPS, never plain text."*
    - **`HttpOnly` lock**: *"Hide this cookie from JavaScript so hacker scripts can't steal it."*

---

### Step 8: Security Headers (`modules/headers_checker.py`)

* **The Problem:** Before a website sends its webpage, it sends a checklist of safety rules called **Headers**.
* **What the code does:** It checks if the website turned on the 6 most important safety rules:
  1. **CSP**: *"Only load scripts from approved partners."* (Stops hackers from injecting malicious scripts).
  2. **HSTS**: *"Always use HTTPS for the next year—no exceptions."*
  3. **X-Frame-Options**: *"Never let another website put me inside an invisible frame."* (Stops click-jacking scams).
  4. **X-Content-Type-Options**: *"Never guess file types."*
  5. **Referrer-Policy**: *"Don't leak private URLs when users click external links."*
  6. **Permissions-Policy**: *"Keep the microphone and camera turned off."*
* **The Leaks Check:** It also checks if the server is bragging about its software:
  - e.g. `Server: Apache 2.4.1` ⚠️ *(Bad! Tells hackers the exact version to attack).*

---

### Step 9: Detecting What Software It Runs (`modules/tech_detector.py`)

* **The Problem:** What building blocks is the website made of? Is it WordPress? React? Shopify?
* **What the code does:** It searches for clues (fingerprints) in the HTML without doing anything intrusive:
  - If it sees `wp-content/` in the code → It's **WordPress**!
  - If it sees `cdn.shopify.com` → It's **Shopify**!
  - If it sees `__NEXT_DATA__` → It's **React / Next.js**!
  - If the server header says `cloudflare` → It uses **Cloudflare**!

---

### Step 10: The Report Card (`modules/security_scorer.py`)

* **The Problem:** Users don't want to read 100 pages of raw technical data—they want a simple score!
* **What the code does:** It grades the website out of 100 points:
  - **HTTPS**: Up to 20 points
  - **SSL Certificate**: Up to 20 points
  - **Security Headers**: Up to 30 points (5 points for each header)
  - **Cookie Safety**: Up to 10 points
  - **Clean Redirects**: Up to 10 points
  - **No Leaked Server Names**: Up to 10 points
* **Letter Grades:**
  - `90 - 100` = **A+** 🌟
  - `80 - 89` = **A** 🟢
  - `70 - 79` = **B** 🔵
  - `60 - 69` = **C** 🟡
  - `50 - 59` = **D** 🟠
  - Below 50 = **F** 🔴

---

### Step 11: Creating the Excel File (`modules/excel_exporter.py`)

* **The Problem:** Users want to download a clean, professional spreadsheet to show their boss or client.
* **What the code does:** Using the `openpyxl` library, it builds an Excel file with **6 organized tabs**:
  1. **Executive Summary** (Big score badge and overview)
  2. **Recommendations** (Color-coded action items)
  3. **SSL Certificate** (All crypto details)
  4. **Security Headers** (Which ones passed and failed)
  5. **Network & DNS** (IP addresses and mail servers)
  6. **HTTP & Technology** (Detected tech stack and cookies)
* **The Clever Part:** It builds the spreadsheet directly inside the computer's memory (`io.BytesIO`) and streams it right to your browser—so no temporary files are left cluttering the computer!

---

## 🖥️ How the Frontend Works (`static/js/script.js`)

When you visit the page in your browser:
1. You type a URL and hit **CHECK WEBSITE**.
2. JavaScript intercepts the click and displays the **animated loading steps** (Validating... Checking SSL... Calculating score...).
3. It sends a message to the Python backend (`POST /api/scan`).
4. When Python replies with the scan results, JavaScript fills in the cards:
   - Green badge for Online 🟢
   - Expiration days for SSL 🔒
   - Fill-in progress bars for each category 📊
5. When you click **"Download Excel"**, JavaScript calls `/api/export/excel`, grabs the file, and triggers a download right in your browser!

---

## 🎯 Summary: Which File Does What?

| File | Job in 1 Sentence |
| :--- | :--- |
| [`app.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/app.py) | The boss that coordinates everything and talks to the web browser. |
| [`config.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/config.py) | The settings notebook (port number, timeouts, scoring rules). |
| [`modules/url_validator.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/url_validator.py) | Cleans messy URLs and blocks hackers from scanning internal computers. |
| [`modules/availability_checker.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/availability_checker.py) | Rings the website's doorbell to check if it's awake and measures speed. |
| [`modules/ip_resolver.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/ip_resolver.py) | Finds the website's numeric street address (IPv4 and IPv6). |
| [`modules/dns_checker.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/dns_checker.py) | Reads the internet phonebook (mail servers, name servers). |
| [`modules/ssl_checker.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/ssl_checker.py) | Checks the website's digital passport and expiration date. |
| [`modules/http_checker.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/http_checker.py) | Checks if HTTPS is forced and inspects cookie locks. |
| [`modules/headers_checker.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/headers_checker.py) | Checks the 6 critical safety shields in HTTP headers. |
| [`modules/tech_detector.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/tech_detector.py) | Detects what software (WordPress, React, Cloudflare) the site uses. |
| [`modules/security_scorer.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/security_scorer.py) | Calculates the final 0–100 score and letter grade. |
| [`modules/excel_exporter.py`](file:///Users/lakkakulasaiakash/Documents/website_checker/modules/excel_exporter.py) | Builds the beautiful 6-tab Excel report. |
| [`static/js/script.js`](file:///Users/lakkakulasaiakash/Documents/website_checker/static/js/script.js) | Powers the interactive browser buttons, animations, and charts. |
| [`static/css/style.css`](file:///Users/lakkakulasaiakash/Documents/website_checker/static/css/style.css) | Makes everything look modern, dark, and sleek. |

---

*Now you know exactly how the entire Website Security Checker works from end to end!*
