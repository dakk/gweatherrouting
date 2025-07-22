---
html_theme.sidebar_secondary.remove:
sd_hide_title: true
---
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.9.0/css/fontawesome.min.css" integrity="sha512-TPigxKHbPcJHJ7ZGgdi2mjdW9XHsQsnptwE+nOUWkoviYBn0rAAt0A5y3B1WGqIHrKFItdhZRteONANT07IipA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<style>
.bd-main .bd-content .bd-article-container {
  max-width: 70rem; /* Make homepage a little wider instead of 60em */
}
/* Extra top/bottom padding to the sections */
article.bd-article section {
  padding: 3rem 0 7rem;
}
/* Override all h1 headers except for the hidden ones */
h1:not(.sd-d-none) {
  font-weight: bold;
  font-size: 48px;
  text-align: center;
  margin-bottom: 4rem;
}
/* Override all h3 headers that are not in hero */
h3:not(#hero h3) {
  font-weight: bold;
  /* text-align: center; */
}
</style>

(homepage)=
# GWeatherRouting: Open-source sailing routing and navigation

<div id="hero">
  <div id="hero-left">  <!-- Start Hero Left -->
    <h2 style="font-size: 60px; font-weight: bold; margin: 2rem auto 0;">GWeatherRouting</h2>
    <h3 style="font-weight: bold; margin-top: 0;">Open-source sailing routing and navigation</h3>
    <p>GWeatherRouting is an open-source sailing routing and navigation software written using Python and Gtk4.</p>
    <div class="homepage-button-container">
      <div class="homepage-button-container-row">
          <a href="https://github.com/dakk/gweatherrouting/releases/download/v0.2.1/GWeatherRouting-x86_64.AppImage" class="homepage-button primary-button"><i class="fa fa-download"></i> Download Appimage</a>
      </div>
      <div class="homepage-button-container-row">
          <a href="./docs/quickstart.html" class="homepage-button-link">Quickstart →</a>
      </div>
    </div>
  </div>
  <div id="hero-right">
    <img src="./_static/images/quickstart/10.gif">
  </div>
</div>



<!-- # Workflow

<p>The DQPU system is composed of 3 actors:</p>
<br>

::::{grid} 1 1 3 3

:::{grid-item}

<div align="center">
<i class="fa fa-user fa-5x"></i><br><br>

<b>Clients</b>: users who need to perform a quantum sampling
</div>

:::

:::{grid-item}
<div align="center">
<i class="fa fa-user-shield fa-5x"></i><br><br>
<b>Verifiers</b>: delegates who check for data validity and detect cheating users
</div>
:::

:::{grid-item}
<div align="center">
<i class="fa fa-cogs fa-5x"></i><br><br>
<b>Samplers</b>: users who run quantum samplers
</div>
:::

::::-->

<!-- ::::{grid} 1 1 2 2

:::{grid-item}  -->

<h3>Contributions</h3>

Contributions and issue reports are very welcome at the
[GitHub repository](https://github.com/dakk/gweatherrouting).
<!-- ::: -->

:::{toctree}
:maxdepth: 1
:hidden:

Documentation<docs/index>
Source Code<https://github.com/dakk/gweatherrouting>
:::
