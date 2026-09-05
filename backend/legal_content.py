"""
Static legal + product pages, served directly from this same free Render
service. Written specifically to satisfy Paddle's domain review checklist
(clear product description + easily-located ToS/Privacy) without needing
a purchased domain -- Paddle already accepted a bare .onrender.com
subdomain for sandbox approval, and a real product page here is what
domain review is actually checking for, not domain ownership per se.

TODO (Francis): SUPPORT_EMAIL below is a placeholder. Replace it with a
real inbox you actually check before submitting this domain to Paddle
for live review -- a support contact that bounces looks worse than no
contact listed at all.
"""

SUPPORT_EMAIL = "support@cloudweaver.dev"  # TODO: replace with a real, checked inbox

_PAGE_STYLE = """
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, sans-serif;
         max-width: 720px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; line-height: 1.6; }
  h1 { font-size: 1.8em; } h2 { font-size: 1.3em; margin-top: 1.5em; }
  code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
  a { color: #2563eb; } footer { margin-top: 3em; font-size: 0.85em; color: #666; }
</style>
"""

ABOUT_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Cloud Weaver</title>{_PAGE_STYLE}</head>
<body>
<h1>Cloud Weaver</h1>
<p><strong>Rent the cheapest verified-available GPU, from your terminal.</strong></p>
<p>Cloud Weaver searches multiple GPU marketplaces (currently Vast.ai and
RunPod), and unlike a plain price-comparison site, it actually attempts
the reservation and runs a boot-time hardware check -- verifying real
power draw and throughput -- before you're ever billed. If a listing
turns out to be unavailable or the hardware is misrepresented, it's
silently skipped and the next-cheapest verified option is used instead.</p>

<h2>Get started</h2>
<pre><code>pip install cloudweaver
cloudweaver login
cloudweaver add-funds 20
cloudweaver run --gpu RTX_4090</code></pre>

<h2>Pricing</h2>
<p>Pay-as-you-go from a prepaid wallet, billed per second of actual GPU
usage. Top up in fixed amounts of $5, $10, $20, $50, or $100. No
subscription, no minimum commitment. See full <a href="/pricing">pricing details</a>.</p>

<h2>A note on the cheapest tier</h2>
<p>The lowest prices come from interruptible/spot capacity, which cloud
providers can reclaim at any time for a higher bidder. If that happens
mid-job, Cloud Weaver detects it automatically and stops billing you
immediately -- you are never charged for compute that was reclaimed
before your job finished.</p>

<footer>
  <a href="/pricing">Pricing</a> &middot;
  <a href="/terms">Terms of Service</a> &middot;
  <a href="/privacy">Privacy Policy</a> &middot;
  <a href="/refund">Refund Policy</a> &middot;
  Contact: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>
</footer>
</body></html>"""

PRICING_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Pricing - Cloud Weaver</title>{_PAGE_STYLE}</head>
<body>
<h1>Pricing</h1>
<p>Pay-as-you-go, billed per second of actual GPU usage from a prepaid
wallet. No subscription, no minimum commitment, no charge for any
reservation attempt that fails our availability/hardware verification --
you're only ever billed for a verified, working machine you actually
used.</p>

<h2>Adding funds</h2>
<p>Top up your wallet in one of five fixed amounts:</p>
<ul>
  <li>$5</li>
  <li>$10</li>
  <li>$20</li>
  <li>$50</li>
  <li>$100</li>
</ul>
<p>Payment is processed by Paddle.com (our merchant of record); all
standard card payment methods Paddle supports are accepted.</p>

<h2>GPU pricing</h2>
<p>GPU rental prices vary by model, provider, and real-time market
availability -- Cloud Weaver searches live marketplace pricing at the
moment you request a machine and charges a margin on top of our own
cost. Run <code>cloudweaver run --gpu &lt;model&gt;</code> to see the
current verified price before committing.</p>

<h2>What you're not charged for</h2>
<ul>
  <li>Any reservation attempt that fails our live availability check
      ("ghost inventory")</li>
  <li>Any machine that fails our boot-time hardware benchmark (power
      draw / throughput below spec)</li>
  <li>Compute time after a provider reclaims an interruptible instance
      mid-job -- see our <a href="/refund">Refund Policy</a></li>
</ul>

<footer><a href="/">Back to Cloud Weaver</a> &middot;
  <a href="/pricing">Pricing</a> &middot; <a href="/terms">Terms</a> &middot;
  <a href="/privacy">Privacy</a> &middot; <a href="/refund">Refund Policy</a></footer>
</body></html>"""

REFUND_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Refund Policy - Cloud Weaver</title>{_PAGE_STYLE}</head>
<body>
<h1>Refund Policy</h1>
<p><em>Last updated: 2026</em></p>

<h2>Wallet top-ups</h2>
<p>Funds added to your Cloud Weaver wallet are used to pay for verified
GPU compute time as you use it. If you have unused wallet balance and
no longer wish to use the service, contact us at
<a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a> and we will refund
your remaining, unused balance.</p>

<h2>Automatic non-billing for failed or interrupted service</h2>
<p>You are never charged in the following situations -- these aren't
"refunds" you need to request, they're built into how billing works:</p>
<ul>
  <li><strong>A listed GPU turns out to be unavailable</strong> when we
      attempt to reserve it ("ghost inventory") -- we silently try the
      next-cheapest verified option, and you're never billed for the
      failed attempt.</li>
  <li><strong>A machine fails our boot-time hardware check</strong>
      (measured power draw or throughput below the advertised spec) --
      same as above, discarded before you're ever charged.</li>
  <li><strong>An interruptible/spot instance is reclaimed by the
      provider mid-job</strong> -- our metering system detects this
      automatically (typically within 5 minutes) and stops billing your
      wallet from that point forward. You are not charged for the time
      after the instance was reclaimed.</li>
</ul>

<h2>Requesting a refund for a billing error</h2>
<p>If you believe you were incorrectly charged for something not covered
above, email <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a> with
your account email and the approximate time of the charge. We aim to
respond within a few business days.</p>

<h2>Chargebacks</h2>
<p>We'd rather resolve a billing problem directly -- please contact us
before filing a chargeback with your card provider, so we can look into
it and refund you directly if something went wrong.</p>

<footer><a href="/">Back to Cloud Weaver</a> &middot;
  <a href="/pricing">Pricing</a> &middot; <a href="/terms">Terms</a> &middot;
  <a href="/privacy">Privacy</a> &middot; <a href="/refund">Refund Policy</a></footer>
</body></html>"""

TERMS_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Terms of Service - Cloud Weaver</title>{_PAGE_STYLE}</head>
<body>
<h1>Terms of Service</h1>
<p><em>Last updated: 2026</em></p>

<h2>1. The service</h2>
<p>Cloud Weaver ("we", "us") operates a broker service that reserves GPU
compute capacity from third-party providers (currently Vast.ai and
RunPod) on your behalf, verifies it against a boot-time hardware check,
and makes it available to you via a command-line tool. We do not
manufacture or directly operate the underlying GPU hardware.</p>

<h2>2. Accounts and wallet</h2>
<p>You add funds to a prepaid wallet before using the service. Usage is
billed per second against that balance. We do not store your full
payment card details -- payments are processed by Paddle.com, acting as
merchant of record for all transactions.</p>

<h2>3. Interruptible capacity and refunds</h2>
<p>Some capacity we broker is interruptible ("spot") and can be reclaimed
by the underlying provider at any time, independent of anything we or
you do. If this happens, we detect it automatically and stop billing
your wallet for that job from the moment of detection onward. We do not
guarantee uninterrupted availability of any specific instance, and we
are not liable for lost work, time, or data resulting from a provider
reclaiming interruptible capacity -- we strongly recommend saving your
own work/progress periodically if running long jobs on this tier.</p>

<h2>4. Acceptable use</h2>
<p>You may not use the service for anything illegal, for cryptocurrency
mining in violation of a provider's own terms, for generating content
that violates applicable law, or in any way that violates the
underlying providers' (Vast.ai, RunPod) own acceptable use policies.
We reserve the right to suspend accounts that violate this section.</p>

<h2>5. No warranty</h2>
<p>The service is provided "as is." We do not warrant that GPU
performance will exactly match a provider's advertised specifications
beyond what our own boot-time benchmark checks for, or that the service
will be uninterrupted or error-free.</p>

<h2>6. Limitation of liability</h2>
<p>To the maximum extent permitted by law, our liability to you for any
claim arising from use of the service is limited to the amount you paid
us in the 3 months prior to the claim.</p>

<h2>7. Changes</h2>
<p>We may update these terms from time to time; continued use of the
service after a change constitutes acceptance of the updated terms.</p>

<h2>8. Contact</h2>
<p>Questions about these terms: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>

<footer><a href="/">Back to Cloud Weaver</a> &middot;
  <a href="/pricing">Pricing</a> &middot; <a href="/terms">Terms</a> &middot;
  <a href="/privacy">Privacy</a> &middot; <a href="/refund">Refund Policy</a></footer>
</body></html>"""

PRIVACY_PAGE = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Privacy Policy - Cloud Weaver</title>{_PAGE_STYLE}</head>
<body>
<h1>Privacy Policy</h1>
<p><em>Last updated: 2026</em></p>

<h2>What we collect</h2>
<ul>
  <li>Your email address (account identification)</li>
  <li>Job/usage records (which GPU, how long, what it cost) -- needed to
      bill your wallet accurately and show your job history</li>
  <li>Payment information -- collected and processed directly by Paddle,
      our merchant of record. We never see or store your full card
      details.</li>
</ul>

<h2>How we use it</h2>
<p>Solely to operate the service: authenticating you, billing your
prepaid wallet, provisioning GPU instances on your behalf, and
responding to support requests.</p>

<h2>Third parties we share data with</h2>
<ul>
  <li><strong>Paddle.com</strong> -- payment processing, as merchant of
      record for all transactions.</li>
  <li><strong>Supabase</strong> -- our database provider, hosting
      account and usage records.</li>
  <li><strong>Vast.ai / RunPod</strong> -- receive only what's needed to
      provision a machine on your behalf (an SSH public key, not your
      personal account details).</li>
</ul>
<p>We do not sell your data to anyone.</p>

<h2>Data retention</h2>
<p>We retain account and usage records for as long as your account is
active, and as needed to comply with tax/financial recordkeeping
obligations after that.</p>

<h2>Your rights</h2>
<p>You can request a copy of your data or request deletion of your
account by emailing <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.</p>

<h2>Contact</h2>
<p><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>

<footer><a href="/">Back to Cloud Weaver</a> &middot;
  <a href="/pricing">Pricing</a> &middot; <a href="/terms">Terms</a> &middot;
  <a href="/privacy">Privacy</a> &middot; <a href="/refund">Refund Policy</a></footer>
</body></html>"""
