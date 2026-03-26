---
url: https://tante.cc/2026/01/05/exiting-the-billionaire-castle/
title: Exiting the Billionaire Castle
domain: tante.cc
category: tech-criticism
source: rss
date_scanned: 2026-03-08T08:09:39.609271
word_count: 4848
paywall: False
---

# Exiting the Billionaire Castle

**URL:** https://tante.cc/2026/01/05/exiting-the-billionaire-castle/

**Domain:** tante.cc

**Category:** tech-criticism

**Source:** RSS Feed

**Scanned:** 2026-03-08T08:09:39.609271

**Word Count:** 4848

---

Exiting the Billionaire Castle

Jan 5, 2026

—

by

tante

in

english

In 2025 I have spend some time to untangle my digital life from billionaire/fascist (that Venn diagram is becoming more of a circle each and every day) run platforms. So at the beginning of 2026 maybe it makes sense to talk a bit about what I did, why I went certain ways and what works and what doesn’t.

There are a few caveats. I am a trained computer scientist, I financed a lot of my university years by running people’s server infrastructure and I have been running some of my own for more than 2 decades now. My personal computers all run Linux so I am not bound to any proprietary platform like Micro

soft

slop’s or Apple’s  I also am employed and have some disposable income which allows me to acquire hardware etc. So take that into consideration when evaluating my steps.

Also: This is not a howto. I think that infrastructures are deeply personal because our needs and wants are personal. The way we have pushed for a harmonization of everyone’s digital life through centralized platforms for the last decades has been a deeply inhumane endeavor. So what works for me might not at all work for you. Some things might though.

My Infrastructure pre Migration

I used a lot of Google’s services: Gmail for Email (with my own domain though), Google Photos for photo archival and sharing, Google Drive for Storage (since I already paid for extra Google Storage to keep my photos around) and Google Docs for writing, presentations etc. I had a free tier of Dropbox around for some secondary backup of encrypted data. Since I paid for Youtube to get rid of Ads I used Youtube Music for music streaming. I used Notion for notetaking/workflows etc.

For instant messaging I kept around accounts on basically all relevant services (WhatsApp, Signal, Telegram, FB Messenger, etc.) to be reachable by my contacts who all have their preferences. I had already been running my own XMPP and Matrix servers though that got mostly homeopathic action though.

I was already hosting this website (and a few other things) on a root server I was renting at a German provider. Some code I published lived on GitHub.

I had already stopped using my Twitter account after Elon Musk took over and moved most of my social media use to

Mastodon

and a bit of

Bluesky

.

My Migrations

I’ll try splitting this block up a bit into coherent segments for easier reading/skimming.

Domain

I had already used my own domain for a long time (multiple actually). If you have any form of online presence and it’s fully dependent on the goodwill of rich people maybe get your own name on the internet, even if just to redirect it for now. I cannot stress how relevant that is. Your “$name.substack.com” is not yours.

I personally buy my domains at

INWX

, a registrar in Berlin (which coincidentally has their offices right opposite to my day job’s office, I used them before our offices moved there though). INWX basically only offers domains so it’s a bit of an expert thing, you can also get a domain when renting Webspace somewhere for example, might be less hassle.

Email

I evaluated many different providers and self-hosting. Let’s start there: Self-hosting.

Self-hosting email is a pain in the ass. I do it for a legacy client and it’s a fucking clusterfuck (maybe due to his business domain but that’s not for here ;)). I do not need another job of cleaning up the mess when the big providers like Google or Microsoft start fucking around with smaller servers. The problem with email is that it kinda fails silently if you are not putting a lot of attention/work into it while it also being the anchor for almost anything (think account recovery, getting emails from your provider that your server will be shut down, etc). So self-hosting was more of a pain and a source of stress than I was willing to take on – my life is stressful enough.

When it came to evaluating different email providers I had the choice between the super privacy/encryption focused services like

Proton

or

Tuta

or more traditional offerings like

Mailbox

,

Posteo

or

Fastmail

. I like encryption as much as the next person but I shied away from Proton and Tuta because they require an extra, non-standard software to communicate with the server which is a bit too flimsy for my tastes. I’m an old man I like IMAP over transport encryption thankyouverymuch.

Both Mailbox and Posteo have the advantage of being run by German companies on German servers (under EU legislation) which is neat. Both are good choices.

I went with Fastmail

though. They are an Australian company but are very focused on providing just what I need (good, standards based email, calendar and contact management) for a very fair price. Mailbox was a close second but I have a lot of email that I keep dragging around and Mailbox’s plans don’t have the storage I need. Fastmail also makes keeping some Google services around very easy: It continuously imports emails that hit your Gmail inbox (even with me switching my domain over to Fastmail some accounts are bound to my Google account and therefore hit the Gmail inbox) and it allows to use Google calendars seamlessly in their interface which I need since I have a shared calendar with my partner there.

The service itself works flawlessly and even has some cool features (their masked email implementation is great) and I could bring a whole bunch of domains in without any issue. My only issue is that Fastmail is an Australian company that hosts their servers in data centers in the US. That’s not great given the state of the world and might force me to switch at some point. But currently I am very happy with it. Migration was simple and the service mostly works better than Gmail.

Cloud Storage

I had done some tests with different solutions allowing one to set up their own cloud, some of them being rougher than others. So after that it was kinda obvious to me to

go for

Nextcloud

due to it being open source, it being mature software and it having a big community of contributors. I evaluated renting a Nextcloud instance somewhere (there are many companies offering) but with me already paying for a root server (for this website for example) it made sense to just host it myself. This also mitigates the whole “someone else might be reading my files” kind of thread mode. I went for the

Nextcloud AIO docker

route for hosting: Most relevant parameters are set in a convenient way and I don’t have to worry about incompatibilities between different parts of the software stack.

Setup is really easy but if you want to host your own file storage make sure you have some offsite backup set up (which I already had for my server). No a RAID is not a backup.

For mere file storage and sync it works great. There’s clients for every operating system that just syncs your whole storage (or selected paths) down to your machine and let’s you work on stuff. Synchronization issues can appear when two machine open the same document locally but that’s not Nextcloud’s fault. Cleaning up those cases is not hard though.

Nextcloud also offers access via WebDAV which allows my ebook reader to load books from my digital library without having to sync it in full so that was a huge added benefit.

Nextcloud also offers calendar and contact management but I already use the Fastmail provided solutions for that. I will set up a sync from Fastmail to my Nextcloud in the next weeks though for backup purposes.

Cloud Documents

I was a heavy Google docs user. At work I have to use MS 365 but the collaboration features work spotty at best. But both were no options so I looked into what was available on Nextcloud (since I was already hosting that). There’s basically Collabora (based on Libreoffice) and OnlyOffice.

Onlyoffice might look a bit cleaner but it’s a project/company that actively hides its Russian origins and given the actions of Russia lately I am not comfortable integrating that kind of thing into my workflow.

I had already used Libreoffice on my Linux machine for light editing so I went for

Collabora which Nextcloud integrates seamlessly.

It’s not Google Docs. Synchronization sometimes feels a bit fragile, the interface isn’t as clean (it’s gotten

a lot better

though lately). Google Docs really was my sweet spot between features and simplicity (probably because I used it for so long). So switching added some friction. Less so with the document editor for writing but with the spreadsheet and presentation applications: The presentation software works very differently from Google Sheets and changing themes is a lot clunkier. There are more features but the Interface is very much an acquired taste. The spreadsheet application works but Google Sheets was a lot easier to program (that might be me being used to it though).

After a few months I have now kinda gotten used to the Collabora stack. It works, it imports all your word files and whatnot. I sometimes wished I could have the simplicity of the Google Docs suite back.

But I have used it with external collaborators (think editors for articles etc) and didn’t have any issues or receive any complaints. Just be aware that it’s less clean than Google Docs. And I probably would not edit a very long document with a large amount of people there.

I did not evaluate purely text-based platforms like Cryptpad et al because I need a presentation and spreadsheet solution and didn’t want to hack that somehow into markdown editors. As I said: I am an old man with limited free time.

Photos

Looking for a Google Photos replacement is very easy these days:

Immich

just does the job.

It’s basically a self-hosted full clone of Google Photos including shared albums, location tagging and face recognition. So you get all the features of Google Photos without training Google’s AI. Cool.

But Photos take up a lot of space so hosting it yourself can become quite expensive depending on what infrastructure you have access to. The machine learning features need a bit of a capable processor and it has modest RAM requirements so pricing for hosting often starts out at 10 bucks a month depending on the storage you need. Hosting your photos yourself has its advantages but paying Google or Apple will probably be cheaper.

In order to fully migrate my Google Photos I got myself a

Google Photos Takeout

which ended up being a bit over 150GB split over a few archives. I uploaded those to my server and fed them to

immich-go

which can automatically import not just the images but also the meta information (such as albums etc.).

Immich has a great mobile app for Android so my photos automatically get backed up without me even thinking about it. It’s basically a an almost perfect replacement. Some people like

Ente

which does even more encryption and whatnot but I didn’t need the extra complexity given I run all this on my own server. I am hosting Immich via their

docker installation

.

Notes/Workflows

I had a lot of sorta complex data bases and workflows set up on Notion for note-taking and keeping track of ToDos etc. But Notion is kind of a non-product. It keeps you building processes and structures that are never fully what you want so you can

play productivity

a lot. While Notion might not be owned by a classic billionaire from what I know it’s still a service that pushed their AI slopware a lot and is fully US-focused so change made sense.

I looked at many more or less complex self-hosted Notion alternatives such as

Affine

or

Capacities

but those again keep you playing on the meta level instead of focusing in what you need: They push you into creating huge note graveyards that don’t work for me.

So I went back to the drawing board and ended up not running another app but go with Nextcloud again:

The

Nextcloud Deck

app gives me Kanban boards

that suffice for my own ToDo management. I stripped down my own

note taking and went for

Nextcloud Collectives

which is sort of a Wiki with templates for new pages that you can define yourself. When playing around I realized that I could throw away most of the Notion scaffolding and just use wiki pages (which end up technically being markdown text files in my Nextcloud).

This setup works for me right now. I don’t know if I am 100% happy with this and I might look into it more in the next months. But this process has led me to focusing on simpler tools instead of those “second brain” things that kinda fill your day with busywork. That might be my bias though.

But the simple Nexcloud approach works right now and was a good reset for how to think about my own infrastructure. Maybe cloning big corporate systems isn’t the way to go? Maybe decomputing is a better mode of thinking? Still not 100% sure where to land with this. The Nextcloud Apps don’t have mobile apps which can be a bummer and Collectives has a somewhat weird UI that one needs to get used to. But it’s working right now.

Code

Github still is the 800 pound gorilla when it comes to hosting code. Which I don’t do too much of but I have some repositories online that others use.

But given that Microslop is not only billionaire-owned and Trump aligned bit also one of the biggest unlicensed users of people’s source code for their slop generators (“AI”) I thought it might make sense to get my code to a less shady part of the Internet.

There is of course

GitLab

that one can host instead of using GitHub but GitLab is rails (which I don’t particularly like hosting) and GitLab is also pushing “AI” hard. I kinda cast it aside quickly.

The two other alternatives I found were either hosting my own

Forgejo

instance or finding one to use. I landed on the second option:

Codeberg

is a Forgejo instance run by a German association that residing about 10 minutes by bike from my home. They are very serious about community governance, proper processes (aside from just software development processes) and don’t think giving all code to Microsoft for free for them to make Code quality worse all over the planet is a good idea so they are the perfect solution. (I had given them some donations in the past but paused writing this to join the association so you could consider me biased now maybe? I dunno.)

So yeah. For hosting of code I use Codeberg.

Social Media

As I wrote I was already somewhat out of the billionaire hellhole. Twitter used to be my main social presence (with more than 35k followers) but I dropped it like a bad habit when Musk took over. So

my main social is

Mastodon

on an instance I help administer. I do have a

Bluesky

account, too, but I do not trust that network all too much. The developers are basically blockchain people with money from Blockchain companies. Never a good sign. But it’s fun while it lasts right now. I just won’t get too attached to it, but it’s good to keep an eye on whether that system will at some point actually decentralize.

I also am still on LinkedIn which is billionaire owned. It sucks but it’s relevant for my job and my freelance activities. Would love to see it burn in hell but right now I can’t leave.

I still have a Facebook account (cause it’s a platform some relatives might use to contact me). I do no longer have the Facebook apps installed on my phones or use the website regularly. I check in every quarter or so to see if some aunt from overseas send me a message. The account is still alive because some third party accounts use it as login provider. I also have an Instagram account that I only use to follow tattoo artists (who sadly all just live on Instagram). Sucks but there literally is no alternative. I do not use other image-based social media sites (like Pixelfed) because personally I realized that these platforms just give me anxiety and a low self opinion even if they are open source and whatnot (insert joke about the open source Torment Nexus here).

I have never used TikTok so I didn’t need any migration.

Web search

This one I did not expect to get to this year. I had always used Google Search but with their recent strategy of poisoning their own search results with incorrect slop (“AI”) it became unbearable to keep using it as a tool to find information. The problem is that building and updating a search index is really expensive which means that many search engines are basically just frontends for Google’s or Bing’s or Yandex’s index.

Be that as it may I went through a few trials. I tested

Qwant

, a French search engine, but the results were … not great for me. There’s

Ecosia

whose results were okayish and which claims to somehow plant trees from your searches – which is good! – but which is also increasingly deploying AI features that undermine the “saving the forest” narrative a bit.

DuckDuckGo

‘s search quality is kinda like Ecosia – okay but not great. Also very slop-focused. As they all seem to be.

I finally landed (for now) on

Kagi

– which I do pay for. It is a US company (not great), also does a lot of “AI” shit including a browser but the slop generator can be easily disabled at least. The search quality is basically where Google used to be before they decided that having the best Search Engine on the planet wasn’t a good business model.

The decision for Kagi isn’t set in stone though. Being US based is an issue and the CEO seems to be a weirdo with quite a few bad takes. Would be happy to pay for a company’s search services that do not burn money on “AI” nonsense but just build a good search experience. I do find having a search engine I do not have to fight to get the ads out very relaxing though.

Browser

I fully switched back to

Firefox

a few years ago when Google started to limit ad blockers in Chrome, so not much changed this year. But Mozilla is fully depending on their contract with Google making them at least billionaire adjacent and just installed a new CEO who is all in on “AI” instead of the open web so I don’t see this lasting forever. But right now the only way to not depend on Google directly is Firefox, all other browsers are just Chrome wrappers. Except Safari maybe but that is not available on the platforms I use and also … not a very good browser.

We can only hope that some new, open source browser that’s not run by people who’d rather work at a startup gains enough traction to become an alternative. The best chance for that right now is

Servo

who I have given money to and keep a close eye on. It’s just far from ready.

Music Streaming

As I wrote I used Youtube Music cause it’s included in my Youtube subscription. But with trying to get away from billionaires as much as possible looking at this made sense. Also: Youtube Music pays out to the artists as bad as Spotify. And while YT Music might not generate AI slop to steal even more from artists or spend their profits on weapons manufacturers or fascists it’s still bad.

There are not too many options: I settled on

Qobuz

which not only has better audio quality than YT Music but also pays artists significantly more. Qobuz isn’t as heavily algorithmified as most music streaming platforms and focuses more on artists and albums which I enjoy and which corresponds to my listening habits. They do have some holes in their catalogue though.

This lead me to set up a streaming server on my own network:

Jellyfin

. I got out my portable blueray thingy and ripped CDs and my DVDs like it was 2005 so now I also got a lot of stuff available that was an issue before. I am looking towards shifting more and more media consumption towards my own library and maybe stopping using music streaming instead going for buying albums on bandcamp or the likes. We’ll have to see how this space develops.

This does have the added benefit of me being able to curate a controlled library of kid friendly shows for my son that he can watch in his media time.

Misc Services

There are many services that one sometimes used to use that often integrate well with Google’s infrastructure. I sometimes used Google Forms to collect data, I used Doodle to figure out dates.

Currently I migrated most of those apps to their Nextcloud counterparts: I use

Polls

as Doodle replacement,

Forms

instead of Google Forms and

Cospend

to split bills.

This does

work

, it often is a lot less convenient though. Things don’t have simple to use mobile apps, the UI hasn’t gone through 10 rounds of A/B testing. On the other hand the only dark patterns in there are just bugs. So I can live with it.

The Challenges Ahead

As I wrote in the beginning: This is all a work in progress. Many things I landed on I might change, not everything feels great TBH.

Also: People underestimate the cost of all this. Not just the financial burden (though there is quite a bit of that!) but also the extra work I put on myself. I now have to maintain even more software, software I do depend on, with data I want to keep safe. For me it’s not unbearable and sometimes it’s fun (remember? Computers used to be fun at some point) to get a thing working exactly the way you want it to. But it’s not free – even if the software doesn’t cost you anything.

Also: Currently I run those services

for me

(okay, my XMPP and Matrix servers have a few accounts for friends and I do host a few extra websites on my server). But a lot of software, especially cloud software is built around facilitating sharing and collaboration. For me that mostly means with either my partner or with people I write for.

The “people I write for” thing is mostly covered I think. But I am somewhat hesitant about bringing my partner in. For photos I think she’ll be fine, Immich works. But when it comes to calendars and all that I am glad that Fastmail allows me to just keep maintaining the shared calendar as a Google Calendar and not burdening her with how to setup a CalDAV server on her devices. Not cause she isn’t competent but because she’s got shit to do and I am not sure I want to be on call every time some software fails. When it’s Google’s software I can at least just shrug and wonder if they vibecoded it.

I am also stuck with an Android phone because other mobile operating systems often do not support apps I rely on (for example for my bank account etc.).

For online payment I am also often forced to use PayPal which I have not really found a good alternative for.

So there’s a lot of stuff still to do, to figure out. But I got some stuff done at least. And while it is a lot of work, thinking about the types of infrastructures we want and need is good. Especially when you allow yourself not just to install some open source clone of whatever Google or Microsoft product you used to use but actually rethink what you want your computing to be like.

Liked it? Take a second to support tante on Patreon!

This work is licensed under a

Creative Commons Attribution-ShareAlike 4.0 International License

.

Fediverse reactions

1 quote

Discover more from Smashing Frames

Subscribe to get the latest posts sent to your email.

Type your email…

Subscribe

Comments

16 responses to “Exiting the Billionaire Castle”

Liz

January 6, 2026

Reading this article I discovered that it mostly matches with my plans – but you are much further than I am 😉 But that convinces me that personal decisions like Nextcloud and Immich seem to be a good way. And it reminds me to take a look into the email providers, because I am also currently relying on Google for calendars – which is damn convenient. My primary email has already been moved away from MS to an own domain mail, managed by Strato. But while that is sufficient for my personal email organization, that does not seem to offer a nice calendar manager. Hmpf.

So much stuff to do … But not to forget: It is also fun!

Liberation from Big Tech? – Nick's Blog

January 6, 2026

[…] by

https://tante.cc/2026/01/05/exiting-the-billionaire-castle/

I decided to write a post detailing my own attempts to stop using Big Tech […]

Anonymous

January 6, 2026

Great article, I learned things, also on my way to leave the castles, thank you. Immich is great.

Regarding Notes/Workflows, I ended up with a git repository containing markdown files and Obsidian.

Leanne

January 6, 2026

Question: you didn’t mention Vivaldi when discussing web browsers. In my admittedly limited amount of searching in trying to find an alternative to Chrome, this one kept coming up as a good choice where the owners have taken a stance against AI. Is this not an actually good alternative?

tante

January 6, 2026

Vivaldi also is basically Google Chrome in a trench coat. That’s why I don’t consider it an alternative

Schoemi

January 7, 2026

What are your thoughts or plans on the messenger topic?

I use Signal whenever I can, but there a so many non-tech related groups where there is simply no alternative to WhatsApp (like sports club, kid’s school, band, etc.)

Liz

January 7, 2026

What’s with Threema? In my opinion this is the only “not big tech” alternative, because Signal is also hosted on AWS etc. in the end and although it currently is a foundation, it could also end like WhatsApp.

tante

January 7, 2026

I migrated most of my chats to Signal but as you wrote: I live in this world and daycare and other existing structures use WhatsApp. So I keep most existing messengers around. I did kill FB Messenger though.

Scott

January 7, 2026

There are some interesting peer to peer chat apps worth investigating. Keet and Jami are the two I have had most success with.

Sabine

January 7, 2026

re social media:

Maybe consider giving spoutible.com a try. Existing since Feb 2023 it proves that social media can exist without an algorithm, provides all the tools you expect with a modern social media platform and keeps trolls, haters and troublemakers at bay. Moreover, it allows no porn and advertising is light. It is not owned by big money or investors, but relies on its own funds (a lot of users are investors in that site, BTW).

It is social media as it was meant to work and which deserves this name.

Sophia-Croft

January 7, 2026

My spouse picked Proton for his email.

I’m another Spoutible user – in fact, I found your essay from a Spoutible post.

I do so much more communication and chatting on Spoutible than I do on Bluesky

13reak

January 8, 2026

@blog

Great article!

I migrated from PayPal to Wero. It works well with me, although not very many people have it yet. However, I see it growing. More and more people have it automatically because more European banks support Wero.

My last problem is Android. I’m not sure if I will kill too many apps (online banking as you said), if I switch to a custom ROM.

tante

January 8, 2026

Would love to try Wero but my bank doesn’t support it 🙁

13reak

January 8, 2026

@blog

Mine too, so it was time for a new bank. (You don’t have to delete your old one, I mean PayPal you had additionally to your bank account too).

I actually like it this way cause I only have a few euros on it. Even if someone scams me or hacks Wero, they can only steal a couple of euros.

Kyrielle

January 8, 2026

Re browsers – I have a friend who swears by Waterfox, which is a Firefox fork. Maybe it would also work for you?

lieblingswelt

January 23, 2026

@blog

thanks 🙏
