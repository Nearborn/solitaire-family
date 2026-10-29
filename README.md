# Solitaire Family — 18 games

A free, ad-free, noncommercial Pygame Solitaire collection for Samsung Galaxy phones and tablets, distributed as a progressive web app.

## Complete publishing setup

The GitHub Actions workflow is configured. **The source archive still needs to be uploaded to this repository.**

1. Download `Solitaire_18_Games_Android_PWA_v1_3.zip` from the ChatGPT conversation.
2. In this GitHub repository, choose **Add file → Upload files**.
3. Upload the ZIP **without extracting or renaming it** to the root of the repository, and commit it to `main`.
4. In **Settings → Pages → Build and deployment**, select **GitHub Actions**.
5. Open **Actions → Build and publish Solitaire PWA** and confirm that the test, build, and deployment jobs succeed. If needed, run the workflow manually.

When deployed, the game will be at https://nearborn.github.io/solitaire-family/.

On Samsung Galaxy, open the URL in Chrome, use **Add to Home screen** or **Install app**, and test game controls. The first launch requires internet; offline behavior remains unverified.

The included `Solitaire/LICENSE.txt` retains the upstream PolyForm Noncommercial license. The browser build has not yet been validated on real Android hardware.
