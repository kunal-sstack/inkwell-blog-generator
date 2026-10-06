import { ChangeDetectorRef, Component, inject, provideZonelessChangeDetection } from '@angular/core';
import { bootstrapApplication } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { HttpClient, provideHttpClient } from '@angular/common/http';

interface Draft { content: string; words: number; reading_minutes: number; demo: boolean }
@Component({
  selector: 'app-root', standalone: true, imports: [FormsModule],
  template: `
    <header><a class="brand" href="/">◈ <span>inkwell</span></a><span class="header-label">YOUR PERSONAL BLOG STUDIO</span><span class="badge">✦ Powered by LangChain</span></header>
    <main><section class="intro"><div class="eyebrow">A LITTLE IDEA. A GREAT STORY.</div><h1>Find your words.<br><span>Make them matter.</span></h1><p>Turn a spark of inspiration into a thoughtful blog.<br>Bring the idea. We’ll help with the first draft.</p></section>
    <div class="workspace"><section class="brief card"><div class="section-heading"><span class="step">01</span><div><h2>The creative brief</h2><p>Give your story a little direction.</p></div></div>
    <form (ngSubmit)="generate()" #form="ngForm">
      <label for="topic">What’s on your mind? <span>*</span></label><textarea id="topic" name="topic" [(ngModel)]="brief.topic" required minlength="3" maxlength="300" placeholder="e.g. How small daily habits can change your life" rows="3"></textarea>
      <label for="audience">Who are you writing for?</label><input id="audience" name="audience" [(ngModel)]="brief.audience" maxlength="150" placeholder="e.g. Busy professionals, curious beginners">
      <div class="fields"><div><label for="tone">Tone of voice</label><select id="tone" name="tone" [(ngModel)]="brief.tone"><option>Conversational</option><option>Professional</option><option>Inspiring</option><option>Educational</option></select></div><div><label for="length">Article length</label><select id="length" name="length" [(ngModel)]="brief.length"><option value="Short">Short · ~400 words</option><option value="Medium">Medium · ~800 words</option><option value="Long">Long · ~1,200 words</option></select></div></div>
      <label for="keywords">Keywords <small>OPTIONAL</small></label><input id="keywords" name="keywords" [(ngModel)]="brief.keywords" maxlength="300" placeholder="Add a few keywords, separated by commas">
      <label for="notes">Anything else? <small>OPTIONAL</small></label><textarea id="notes" name="notes" [(ngModel)]="brief.notes" maxlength="2000" placeholder="An angle to explore, points to include…" rows="2"></textarea>
      <div class="mode"><label><input type="checkbox" name="demo" [(ngModel)]="brief.demo"> Try demo mode</label><span>{{brief.demo ? 'No API key needed' : 'Gemini via LangChain'}}</span></div>
      <button class="generate" type="submit" [disabled]="loading || form.invalid || brief.topic.trim().length < 3">{{loading ? 'Writing your story…' : '✦ Generate my blog'}} <span>↗</span></button>
      @if (error) { <p class="error" role="alert">{{error}}</p> }
      <p class="footnote">Your next great post starts with a first draft.</p>
    </form></section>
    <section class="output card" [attr.aria-busy]="loading"><div class="output-header"><div class="section-heading"><span class="step">02</span><div><h2>Your next story</h2><p>{{draft ? (draft.demo ? 'Sample draft · demo mode' : 'AI draft · ready for your edits') : 'A blank page, full of possibility.'}}</p></div></div>@if(draft){<div class="actions"><button type="button" (click)="copy()">{{copied ? 'Copied!' : 'Copy'}}</button><button type="button" (click)="download()">↓ .md</button></div>}</div>
    @if (draft) {<div class="stats">{{draft.words}} words <span>·</span> {{draft.reading_minutes}} min read <span>·</span> Markdown</div><textarea class="draft" aria-label="Edit your blog draft" [(ngModel)]="draft.content"></textarea><div class="draft-note">Make it yours. Review facts and add your own perspective before publishing.</div>}
    @else {<div class="empty"><div class="illustration">✎</div><h3>{{loading ? 'Good stories take a moment.' : 'Your ideas belong here.'}}</h3><p>{{loading ? 'Shaping your brief into a fresh first draft…' : 'Fill in your brief and watch your next blog come to life.'}}</p><div class="empty-tags"><span>✧ Your voice</span><span>☰ Clear structure</span><span>↗ Fresh ideas</span></div></div>}
    </section></div><footer>MADE FOR THE MOMENTS WHEN INSPIRATION STRIKES.<span>Python + LangChain + Angular</span></footer></main>`
})
class App {
  private http = inject(HttpClient);
  private changeDetector = inject(ChangeDetectorRef);
  brief = { topic: '', audience: '', tone: 'Conversational', length: 'Medium', keywords: '', notes: '', demo: false };
  draft: Draft | null = null; loading = false; error = ''; copied = false;
  generate() {
    this.loading = true; this.error = ''; this.copied = false;
    this.http.post<Draft>('/api/generate', this.brief).subscribe({next: result => {this.draft = result; this.loading = false; this.changeDetector.markForCheck();}, error: err => {this.error = typeof err.error?.detail === 'string' ? err.error.detail : 'Could not reach the blog service. Make sure the Python backend is running.'; this.loading = false; this.changeDetector.markForCheck();}});
  }
  async copy() { try { await navigator.clipboard.writeText(this.draft?.content || ''); this.copied = true; } catch { this.error = 'Clipboard access is unavailable. Select the draft and copy it manually.'; } this.changeDetector.markForCheck(); }
  download() { const url = URL.createObjectURL(new Blob([this.draft?.content || ''], {type:'text/markdown'})); const link = document.createElement('a'); link.href = url; link.download = 'inkwell-blog.md'; link.click(); URL.revokeObjectURL(url); }
}
bootstrapApplication(App, {providers: [provideHttpClient(), provideZonelessChangeDetection()]}).catch(console.error);
