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
  text-align: center;
}
</style>

(homepage)=
# GWeatherRouting: Open-source sailing routing and navigation

<div id="hero">

<div id="hero-left">  <!-- Start Hero Left -->
  <h2 style="font-size: 60px; font-weight: bold; margin: 2rem auto 0;">GWeatherRouting</h2>
  <h3 style="font-weight: bold; margin-top: 0;">Open-source sailing routing and navigation</h3>
  <p>GWeatherRouting is an open-source sailing routing and navigation software written using Python and Gtk4.</p>

<!-- <div class="homepage-button-container">
  <div class="homepage-button-container-row">
      <a href="./docs/qiskit_example.html" class="homepage-button primary-button">Get Started</a>
      <a href="https://dqpu.io/app" target="_blank" class="homepage-button secondary-button">App UI</a>
  </div>
  <div class="homepage-button-container-row">
      <a href="./docs/index.html" class="homepage-button-link">See Documentation →</a>
  </div>
</div> -->
</div>  <!-- End Hero Left -->
<!-- <div id="hero-right">

<!-- ```bash
pip install dqpu
```

```python
from dqpu.backends.qiskit import DQPUBackend

backend = DQPUBackend()
backend.load_account("dqpu_alice.testnet")

job = backend.run(quantum_circuit, shots=1024)
counts = job.result().get_counts(circ)
```

</div> -->

</div>  End Hero -->



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

::::


The following process outlines how clients can submit quantum circuits for sampling using the DQPU contract on NEAR blockchain:

1. **Client Submits Job**: A *Client* sends a quantum circuit along with a reward to the DQPU smart contract

2. **Verifier Validates Circuit**: A *Verifier* validates the submitted circuit adding `trap qubits`

3. **Simulation or Hardware Execution**: A *Sampler* executes the job retrieved from the waiting list and submit the result

4. **Verifier Checks Result**: The *Verifier* checks result validity and the rewards are distributed

5. **Client Receives Result**: The *Client* can retrieve the final result from the smart contract.

Read the extended workflow from the [README Workflow section](https://github.com/dakk/dqpu?tab=readme-ov-file#workflow)


# Support DQPU

::::{grid} 1 1 2 2

:::{grid-item} -->

<h3>Contributions</h3>

Contributions and issue reports are very welcome at
[the GitHub repository](https://github.com/dakk/gweatherrouting).
:::

:::{grid-item}

<!-- <h3>Citation</h3>

```
  @software{dqpu2024,
      author = {Davide Gessa},
      title = {dqpu: A Web3-Powered, Decentralized Quantum Simulator with Verifiable Computation },
      url = {https://github.com/dakk/dqpu},
      year = {2024},
  }
``` -->

:::

:::{toctree}
:maxdepth: 1
:hidden:

<!-- Getting Started<docs/qiskit_example.ipynb> -->
Documentation<docs/index>
<!-- Node operator<nodes/index> -->
<!-- API<api/index> -->
<!-- App UI<https://dqpu.io/app> -->
Source Code<https://github.com/dakk/gweatherrouting>
:::
