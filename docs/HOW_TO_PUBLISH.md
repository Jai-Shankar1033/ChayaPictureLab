# Recording authorship properly (what actually protects you)

Nothing can stop someone *claiming* your work, but these show who made it and when:

1. Put your real name in `LICENSE` (replace the placeholder).
2. Create a Git history under your own account:
   ```bash
   git init
   git add .
   git commit -m "ChayaPictureLab: initial independent release"
   git branch -M main
   git remote add origin https://github.com/<your-username>/ChayaPictureLab.git
   git push -u origin main
   ```
   Make further small commits as you read the code, fix things or add notes - dated commits show your involvement.
3. Read `docs/viva_questions.md`, run the app, and change something small yourself (a default value, a new test).
   Being able to explain and modify the code is the strongest evidence of ownership.
4. Keep `THIRD_PARTY_NOTICES.md` and `docs/originality_review.md`; they show you credited what you built on.
