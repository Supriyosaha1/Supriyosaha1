# Upload instructions

This folder is ready for the GitHub profile repository:

`Supriyosaha1/Supriyosaha1`

## Upload the files

1. Extract `Supriyosaha1-profile-ready.zip` on your computer.
2. Open `https://github.com/Supriyosaha1/Supriyosaha1`.
3. Choose **Add file → Upload files**.
4. Upload `README.md`, `generate_profile.py`, `dark_mode.svg`, `light_mode.svg`, and the `assets` folder.
5. GitHub's normal Upload files screen may not preserve the hidden `.github` folder. Create the workflow separately with **Add file → Create new file**.
6. Name that file `.github/workflows/profile-card.yml` and paste the contents of the included workflow file.
7. Commit everything to `main`.

## Run it

1. Go to **Settings → Actions → General**.
2. Under **Workflow permissions**, select **Read and write permissions**, then save.
3. Go to **Actions → Update profile card**.
4. Choose **Run workflow → Run workflow**.

The workflow refreshes the public repository count, stars, followers, top languages, and update date every day.

## Important

Do not upload the ZIP itself into the GitHub repository. Upload the files inside it.
