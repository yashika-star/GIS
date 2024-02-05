Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhZDUzZDM2OC1hYzFmLTQ5ZDYtYWYzNy1iZjEzZmE3NTQzOTEiLCJpZCI6MTcyNzU5LCJpYXQiOjE2OTc3MTUxNzh9.-2ecgA5Sb4Q4bYNgjjSm0sgthnHq658-7TUrIzx2yKw';
window.CESIUM_BASE_URL = '/static/cesium/';

var selectors = {
    map: "map"
}

$(document).ready(function () {
    // Initialize the Cesium Viewer in the HTML element with the `cesiumContainer` ID.
    const viewer = new Cesium.Viewer(selectors.map, {
        terrain: Cesium.Terrain.fromWorldTerrain(),
      });

      // Fly the camera to San Francisco at the given longitude, latitude, and height.
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(-122.4175, 37.655, 400),
        orientation: {
          heading: Cesium.Math.toRadians(0.0),
          pitch: Cesium.Math.toRadians(-15.0),
        }
      });

    //   // Add Cesium OSM Buildings, a global 3D buildings layer.
    //   const buildingTileset = await Cesium.createOsmBuildingsAsync();
    //   viewer.scene.primitives.add(buildingTileset);
});