<div class="main" role="main"> <div class="header"> <div class="title"> <h1>Keep a Changelog</h1> <h2>Don’t let your friends dump git logs into changelogs.</h2> </div> <a href="https://github.com/olivierlacan/keep-a-changelog/blob/main/CHANGELOG.md">Version <strong>1.1.0</strong> </a><pre class="changelog" lang="en"># Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- v1.1 Brazilian Portuguese translation.
- v1.1 German Translation
- v1.1 Spanish translation.
- v1.1 Italian translation.
- v1.1 Polish translation.
- v1.1 Ukrainian translation.

### Changed

- Use frontmatter title &amp; description in each language version template
- Replace broken OpenGraph image with an appropriately-sized Keep a Changelog
  image that will render properly (although in English for all languages)
- Fix OpenGraph title &amp; description for all languages so the title and
description when links are shared are language-appropriate

### Removed

- Trademark sign previously shown after the project description in version
0.3.0

## [1.1.1] - 2023-03-05

### Added

- Arabic translation (#444).
- v1.1 French translation.
- v1.1 Dutch translation (#371).
- v1.1 Russian translation (#410).
- v1.1 Japanese translation (#363).
- v1.1 Norwegian Bokmål translation (#383).
- v1.1 "Inconsistent Changes" Turkish translation (#347).
- Default to most recent versions available for each languages.
- Display count of available translations (26 to date!).
- Centralize all links into `/data/links.json` so they can be updated easily.

### Fixed

- Improve French translation (#377).
- Improve id-ID translation (#416).
- Improve Persian translation (#457).
- Improve Russian translation (#408).
- Improve Swedish title (#419).
- Improve zh-CN translation (#359).
- Improve French translation (#357).
- Improve zh-TW translation (#360, #355).
- Improve Spanish (es-ES) transltion (#362).
- Foldout menu in Dutch translation (#371).
- Missing periods at the end of each change (#451).
- Fix missing logo in 1.1 pages.
- Display notice when translation isn't for most recent version.
- Various broken links, page versions, and indentations.

### Changed

- Upgrade dependencies: Ruby 3.2.1, Middleman, etc.

### Removed

- Unused normalize.css file.
- Identical links assigned in each translation file.
- Duplicate index file for the english version.

## [1.1.0] - 2019-02-15

### Added

- Danish translation (#297).
- Georgian translation from (#337).
- Changelog inconsistency section in Bad Practices.

### Fixed

- Italian translation (#332).
- Indonesian translation (#336).

## [1.0.0] - 2017-06-20

### Added

- New visual identity by [@tylerfortune8](https://github.com/tylerfortune8).
- Version navigation.
- Links to latest released version in previous versions.
- "Why keep a changelog?" section.
- "Who needs a changelog?" section.
- "How do I make a changelog?" section.
- "Frequently Asked Questions" section.
- New "Guiding Principles" sub-section to "How do I make a changelog?".
- Simplified and Traditional Chinese translations from [@tianshuo](https://github.com/tianshuo).
- German translation from [@mpbzh](https://github.com/mpbzh) &amp; [@Art4](https://github.com/Art4).
- Italian translation from [@azkidenz](https://github.com/azkidenz).
- Swedish translation from [@magol](https://github.com/magol).
- Turkish translation from [@emreerkan](https://github.com/emreerkan).
- French translation from [@zapashcanon](https://github.com/zapashcanon).
- Brazilian Portuguese translation from [@Webysther](https://github.com/Webysther).
- Polish translation from [@amielucha](https://github.com/amielucha) &amp; [@m-aciek](https://github.com/m-aciek).
- Russian translation from [@aishek](https://github.com/aishek).
- Czech translation from [@h4vry](https://github.com/h4vry).
- Slovak translation from [@jkostolansky](https://github.com/jkostolansky).
- Korean translation from [@pierceh89](https://github.com/pierceh89).
- Croatian translation from [@porx](https://github.com/porx).
- Persian translation from [@Hameds](https://github.com/Hameds).
- Ukrainian translation from [@osadchyi-s](https://github.com/osadchyi-s).

### Changed

- Start using "changelog" over "change log" since it's the common usage.
- Start versioning based on the current English version at 0.3.0 to help
  translation authors keep things up-to-date.
- Rewrite "What makes unicorns cry?" section.
- Rewrite "Ignoring Deprecations" sub-section to clarify the ideal
  scenario.
- Improve "Commit log diffs" sub-section to further argument against
  them.
- Merge "Why can’t people just use a git log diff?" with "Commit log
  diffs".
- Fix typos in Simplified Chinese and Traditional Chinese translations.
- Fix typos in Brazilian Portuguese translation.
- Fix typos in Turkish translation.
- Fix typos in Czech translation.
- Fix typos in Swedish translation.
- Improve phrasing in French translation.
- Fix phrasing and spelling in German translation.

### Removed

- Section about "changelog" vs "CHANGELOG".

## [0.3.0] - 2015-12-03

### Added

- RU translation from [@aishek](https://github.com/aishek).
- pt-BR translation from [@tallesl](https://github.com/tallesl).
- es-ES translation from [@ZeliosAriex](https://github.com/ZeliosAriex).

## [0.2.0] - 2015-10-06

### Changed

- Remove exclusionary mentions of "open source" since this project can
  benefit both "open" and "closed" source projects equally.

## [0.1.0] - 2015-10-06

### Added

- Answer "Should you ever rewrite a change log?".

### Changed

- Improve argument against commit logs.
- Start following [SemVer](https://semver.org) properly.

## [0.0.8] - 2015-02-17

### Changed

- Update year to match in every README example.
- Reluctantly stop making fun of Brits only, since most of the world
  writes dates in a strange way.

### Fixed

- Fix typos in recent README changes.
- Update outdated unreleased diff link.

## [0.0.7] - 2015-02-16

### Added

- Link, and make it obvious that date format is ISO 8601.

### Changed

- Clarified the section on "Is there a standard change log format?".

### Fixed

- Fix Markdown links to tag comparison URL with footnote-style links.

## [0.0.6] - 2014-12-12

### Added

- README section on "yanked" releases.

## [0.0.5] - 2014-08-09

### Added

- Markdown links to version tags on release headings.
- Unreleased section to gather unreleased changes and encourage note
  keeping prior to releases.

## [0.0.4] - 2014-08-09

### Added

- Better explanation of the difference between the file ("CHANGELOG")
  and its function "the change log".

### Changed

- Refer to a "change log" instead of a "CHANGELOG" throughout the site
  to differentiate between the file and the purpose of the file — the
  logging of changes.

### Removed

- Remove empty sections from CHANGELOG, they occupy too much space and
  create too much noise in the file. People will have to assume that the
  missing sections were intentionally left out because they contained no
  notable changes.

## [0.0.3] - 2014-08-09

### Added

- "Why should I care?" section mentioning The Changelog podcast.

## [0.0.2] - 2014-07-10

### Added

- Explanation of the recommended reverse chronological release ordering.

## [0.0.1] - 2014-05-31

### Added

- This CHANGELOG file to hopefully serve as an evolving example of a
  standardized open source project CHANGELOG.
- CNAME file to enable GitHub Pages custom domain.
- README now contains answers to common questions about CHANGELOGs.
- Good examples and basic guidelines, including proper date formatting.
- Counter-examples: "What makes unicorns cry?".

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.1...HEAD
[1.1.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.8...v0.1.0
[0.0.8]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.7...v0.0.8
[0.0.7]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.6...v0.0.7
[0.0.6]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/olivierlacan/keep-a-changelog/releases/tag/v0.0.1
</pre> </div> <div class="answers"> <h3 id="what"> <a aria_hidden="true" class="anchor" href="#what"></a> What is a changelog? </h3> <p> A changelog is a file which contains a curated, chronologically ordered list of notable changes for each version of a project. </p> <h3 id="why"> <a aria_hidden="true" class="anchor" href="#why"></a> Why keep a changelog? </h3> <p> To make it easier for users and contributors to see precisely what notable changes have been made between each release (or version) of the project. </p> <h3 id="who"> <a aria_hidden="true" class="anchor" href="#who"></a> Who needs a changelog? </h3> <p> People do. Whether consumers or developers, the end users of software are human beings who care about what's in the software. When the software changes, people want to know why and how. </p> </div> <div class="good-practices"> <h3 id="how"> <a aria_hidden="true" class="anchor" href="#how"></a> How do I make a good changelog? </h3> <h4 id="principles"> <a aria_hidden="true" class="anchor" href="#principles"></a> Guiding Principles </h4> <ul> <li> Changelogs are <em>for humans</em>, not machines. </li> <li> There should be an entry for every single version. </li> <li> The same types of changes should be grouped. </li> <li> Versions and sections should be linkable. </li> <li> The latest version comes first. </li> <li> The release date of each version is displayed. </li> <li> Mention whether you follow <a href="https://semver.org/">Semantic Versioning</a>. </li> </ul> <a aria_hidden="true" class="anchor" href="#types"></a> <h4 id="types">Types of changes</h4> <ul> <li> <code>Added</code> for new features. </li> <li> <code>Changed</code> for changes in existing functionality. </li> <li> <code>Deprecated</code> for soon-to-be removed features. </li> <li> <code>Removed</code> for now removed features. </li> <li> <code>Fixed</code> for any bug fixes. </li> <li> <code>Security</code> in case of vulnerabilities. </li> </ul> </div> <div class="effort"> <h3 id="effort"> <a aria_hidden="true" class="anchor" href="#effort"></a> How can I reduce the effort required to maintain a changelog? </h3> <p> Keep an <code>Unreleased</code> section at the top to track upcoming changes. </p> <p>This serves two purposes:</p> <ul> <li> People can see what changes they might expect in upcoming releases </li> <li> At release time, you can move the <code>Unreleased</code> section changes into a new release version section. </li> </ul> </div> <div class="bad-practices"> <h3 id="bad-practices"> <a aria_hidden="true" class="anchor" href="#bad-practices"></a> Can changelogs be bad? </h3> <p>Yes. Here are a few ways they can be less than useful.</p> <h4 id="log-diffs"> <a aria_hidden="true" class="anchor" href="#log-diffs"></a> Commit log diffs </h4> <p> Using commit log diffs as changelogs is a bad idea: they're full of noise. Things like merge commits, commits with obscure titles, documentation changes, etc. </p> <p> The purpose of a commit is to document a step in the evolution of the source code. Some projects clean up commits, some don't. </p> <p> The purpose of a changelog entry is to document the noteworthy difference, often across multiple commits, to communicate them clearly to end users. </p> <h4 id="ignoring-deprecations"> <a aria_hidden="true" class="anchor" href="#ignoring-deprecations"></a> Ignoring Deprecations </h4> <p> When people upgrade from one version to another, it should be painfully clear when something will break. It should be possible to upgrade to a version that lists deprecations, remove what's deprecated, then upgrade to the version where the deprecations become removals. </p> <p> If you do nothing else, list deprecations, removals, and any breaking changes in your changelog. </p> <h4 id="confusing-dates"> <a aria_hidden="true" class="anchor" href="#confusing-dates"></a> Confusing Dates </h4> <p> Regional date formats vary throughout the world and it's often difficult to find a human-friendly date format that feels intuitive to everyone. The advantage of dates formatted like <code>2017-07-17</code> is that they follow the order of largest to smallest units: year, month, and day. This format also doesn't overlap in ambiguous ways with other date formats, unlike some regional formats that switch the position of month and day numbers. These reasons, and the fact this date format is an <a href="https://www.iso.org/iso-8601-date-and-time-format.html">ISO standard</a>, are why it is the recommended date format for changelog entries. </p> <h4 id="inconsistent-changes"> <a aria_hidden="true" class="anchor" href="#inconsistent-changes"></a> Inconsistent Changes </h4> <p> A changelog which only mentions some of the changes can be as dangerous as not having a changelog. While many of the changes may not be relevant - for instance, removing a single whitespace may not need to be recorded in all instances - any important changes should be mentioned in the changelog. By inconsistently applying changes, your users may mistakenly think that the changelog is the single source of truth. It ought to be. With great power comes great responsibility - having a good changelog means having a consistently updated changelog. </p> <aside> There’s more. Help me collect these antipatterns by <a href="https://github.com/olivierlacan/keep-a-changelog/issues">opening an issue</a> or a pull request. </aside> </div> <div class="frequently-asked-questions"> <h3 id="frequently-asked-questions"> <a aria_hidden="true" class="anchor" href="#frequently-asked-questions"></a> Frequently Asked Questions </h3> <h4 id="standard"> <a aria_hidden="true" class="anchor" href="#standard"></a> Is there a standard changelog format? </h4> <p> Not really. There's the <a href="https://www.gnu.org/prep/standards/html_node/Style-of-Change-Logs.html#Style-of-Change-Logs">GNU changelog style guide</a>, or the <a href="https://www.gnu.org/prep/standards/html_node/NEWS-File.html#NEWS-File">two-paragraph-long GNU NEWS file</a> "guideline". Both are inadequate or insufficient. </p> <p> This project aims to be <a href="https://github.com/olivierlacan/keep-a-changelog/blob/main/CHANGELOG.md">a better changelog convention.</a> It comes from observing good practices in the open source community and gathering them. </p> <p> Healthy criticism, discussion and suggestions for improvements <a href="https://github.com/olivierlacan/keep-a-changelog/issues">are welcome.</a> </p> <h4 id="filename"> <a aria_hidden="true" class="anchor" href="#filename"></a> What should the changelog file be named? </h4> <p> Call it <code>CHANGELOG.md</code>. Some projects use <code>HISTORY</code>, <code>NEWS</code> or <code>RELEASES</code>. </p> <p> While it's easy to think that the name of your changelog file doesn't matter that much, why make it harder for your end users to consistently find notable changes? </p> <h4 id="github-releases"> <a aria_hidden="true" class="anchor" href="#github-releases"></a> What about GitHub Releases? </h4> <p> It's a great initiative. <a href="https://docs.github.com/en/github/administering-a-repository/releasing-projects-on-github/managing-releases-in-a-repository">Releases</a> can be used to turn simple git tags (for example a tag named <code>v1.0.0</code>) into rich release notes by manually adding release notes or it can pull annotated git tag messages and turn them into notes. </p> <p> GitHub Releases create a non-portable changelog that can only be displayed to users within the context of GitHub. It's possible to make them look very much like the Keep a Changelog format, but it tends to be a bit more involved. </p> <p> The current version of GitHub releases is also arguably not very discoverable by end-users, unlike the typical uppercase files (<code>README</code>, <code>CONTRIBUTING</code>, etc.). Another minor issue is that the interface doesn't currently offer links to commit logs between each release. </p> <h4 id="automatic"> <a aria_hidden="true" class="anchor" href="#automatic"></a> Can changelogs be automatically parsed? </h4> <p> It’s difficult, because people follow wildly different formats and file names. </p> <p> <a href="https://github.com/tech-angels/vandamme/">Vandamme</a> is a Ruby gem created by the Gemnasium team and which parses many (but not all) open source project changelogs. </p> <h4 id="yanked"> <a aria_hidden="true" class="anchor" href="#yanked"></a> What about yanked releases? </h4> <p> Yanked releases are versions that had to be pulled because of a serious bug or security issue. Often these versions don't even appear in change logs. They should. This is how you should display them: </p> <p><code>## [0.0.5] - 2014-12-13 [YANKED]</code></p> <p> The <code>[YANKED]</code> tag is loud for a reason. It's important for people to notice it. Since it's surrounded by brackets it's also easier to parse programmatically. </p> <h4 id="rewrite"> <a aria_hidden="true" class="anchor" href="#rewrite"></a> Should you ever rewrite a changelog? </h4> <p> Sure. There are always good reasons to improve a changelog. I regularly open pull requests to add missing releases to open source projects with unmaintained changelogs. </p> <p> It's also possible you may discover that you forgot to address a breaking change in the notes for a version. It's obviously important for you to update your changelog in this case. </p> <h4 id="contribute"> <a aria_hidden="true" class="anchor" href="#contribute"></a> How can I contribute? </h4> <p> This document is not the <strong>truth</strong>; it’s my carefully considered opinion, along with information and examples I gathered. </p> <p> This is because I want our community to reach a consensus. I believe the discussion is as important as the end result. </p> <p> So please <strong><a href="https://github.com/olivierlacan/keep-a-changelog">pitch in</a></strong>. </p> </div> <div class="press"> <h3>Conversations</h3> <p> I went on <a href="https://changelog.com/podcast/127">The Changelog podcast</a> to talk about why maintainers and contributors should care about changelogs, and also about the motivations behind this project. </p> </div> <footer class="footer clearfix" role="contentinfo"> <img src="/assets/images/keep-a-changelog-mark-f8b06a42.svg" width="30" height="30" class="mark" alt=""> <p class="about"> This project is <a href="https://choosealicense.com/licenses/mit/">MIT Licensed</a> // <a href="https://github.com/olivierlacan/keep-a-changelog/">Created &amp; maintained</a> by <a href="https://olivierlacan.com/">Olivier Lacan</a> <a href="https://ruby.social/@olivierlacan" rel="me" aria-label="Link to Olivier Lacan's Mastodon account"></a> // Designed by Tyler Fortune </p> </footer> </div>
