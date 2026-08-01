# Daily AI Facebook Autoposter

Posts one AI-written caption + AI-generated image to your Facebook Page every
day, automatically, with no manual steps once it's set up.

## How it works
- **GitHub Actions** runs on a daily schedule (free for public repos, and free
  for private repos up to a generous monthly limit).
- Each run calls **Claude** to write a caption in your sewing / personal
  development voice, generates a matching image via **Pollinations.ai**
  (free, no key needed), and posts both to your Page via the **Facebook
  Graph API**.

## One-time setup

### 1. Get a Facebook Page Access Token that won't expire
Regular tokens expire every 60 days. To avoid ever touching this again, use a
**System User** token:

1. Go to [business.facebook.com](https://business.facebook.com) → create or
   open your Business Manager account.
2. Add your Facebook Page to the Business Manager (Business Settings → Accounts → Pages).
3. Business Settings → Users → System Users → **Add** → create a system user
   (Admin role).
4. Assign it your Page (Add Assets → Pages → select your page → Full Control).
5. Click **Generate New Token** for that system user → select your app (create
   one at [developers.facebook.com](https://developers.facebook.com) if you
   don't have one yet, type "Business") → grant `pages_manage_posts` and
   `pages_read_engagement` permissions.
6. Copy the generated token — this is your `FB_PAGE_ACCESS_TOKEN`. System
   user tokens don't expire unless revoked.

### 2. Get your Page ID
Facebook Page → About → scroll down, or use Graph API Explorer
(developers.facebook.com/tools/explorer) with `me/accounts` while logged in
as the system user to list your pages and their IDs.

### 3. Get an Anthropic API key
console.anthropic.com → Settings → API Keys → Create Key.

### 4. Put this code in a GitHub repo
- Create a new **private** repo on GitHub.
- Upload these files (`post_to_facebook.py`, `.github/workflows/daily-post.yml`, this README) keeping the folder structure.

### 5. Add your secrets
Repo → Settings → Secrets and variables → Actions → **New repository secret**,
add all three:
- `ANTHROPIC_API_KEY`
- `FB_PAGE_ID`
- `FB_PAGE_ACCESS_TOKEN`

### 6. Test it
Repo → Actions tab → "Daily Facebook Post" → **Run workflow** (manual
trigger). Check the logs, then check your Page.

Once that works, it'll run automatically every day at the time set in the
workflow file (`cron: "0 10 * * *"` = 10:00 UTC — edit this line to shift the
time; Eldoret is UTC+3, so 10:00 UTC = 1:00 PM local).

## Adjusting content
- Edit the `THEMES` list in `post_to_facebook.py` to change what it writes about.
- Edit the prompt text in `generate_caption()` to tune tone/length/hashtags.
- Posting frequency: change the cron line (e.g. `0 10 * * 1,3,5` = Mon/Wed/Fri).

## Costs
- GitHub Actions: free at this volume.
- Pollinations.ai image generation: free.
- Anthropic API: roughly a fraction of a cent per post (two short Claude calls/day).
- Facebook Graph API: free.
