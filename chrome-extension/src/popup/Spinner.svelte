<!-- A simple spinner component -->
<!-- A circle (dot) in the center and a larger stroked circle around -->
<!-- Then a semicirle that rotates around the center circle like a radar -->

<style>
  .spinner {
    position: relative;
    width: 2rem;
    height: 2rem;
  }

  .circle {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 4px solid rgba(255, 255, 255, 0.25);
    border-radius: 50%;
    z-index: 1;
  }

  .rotating-semicircle {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 4px solid transparent;
    border-top-color: #ffffff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    z-index: 100;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>

<div class="spinner">
  <div class="circle"></div>
  <div class="rotating-semicircle"></div>
</div>
