document.addEventListener('DOMContentLoaded', function () {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    var map = L.map('map').setView([21.8853, -102.2916], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Inicializa el geocoder
    var geocoder = L.Control.Geocoder.nominatim(); // Inicialización

    var currentMarker = null;
    var currentCircle = null;
    var allMarkers = [];
    var allCircles = [];
    var routingControl = null;  


    function clearMap() {
        // Eliminar marcadores del mapa
        if (allMarkers.length > 0) {
            allMarkers.forEach(function(marker) {
                map.removeLayer(marker);  
            });
            allMarkers = [];  
        }
    
        // Eliminar círculos del mapa
        if (allCircles.length > 0) {
            allCircles.forEach(function(circle) {
                map.removeLayer(circle);  
            });
            allCircles = [];  
        }
    
        // Eliminar controles de enrutamiento
        if (routingControl) {
            map.removeControl(routingControl); 
            routingControl = null;  
        }
        document.getElementById('search_results').style.display = 'none';
    
        
    }
const inputField = document.getElementById('search_input');

inputField.addEventListener('input', function() {
    clearMap();


});


    
    document.getElementById('search_input').oninput = function () {
        var query = document.getElementById('search_input').value;
        socket.emit('search', query); 
    };


    document.getElementById('searchBtn').onclick = function () {
        clearMap();
        document.getElementById('search_results').style.display = 'block';
    
        var address = document.getElementById('search_input').value;
        var filteredAddress = address + ', Aguascalientes, Aguascalientes'; // Filtra la búsqueda
        console.log("Buscando: " + filteredAddress);
    
        // Construir la URL para la solicitud de Nominatim
        var nominatimUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(filteredAddress)}&format=json&addressdetails=1`;
    
        // Realizar la solicitud con fetch
        fetch(nominatimUrl)
            .then(response => response.json())
            .then(results => {
                console.log("Resultados de la búsqueda:", results);
                document.getElementById('search_results').innerHTML = ''; // Limpiar resultados previos
    
                if (results && results.length > 0) {
                    results.forEach(result => {
                        var latlng = { lat: parseFloat(result.lat), lng: parseFloat(result.lon) };
                        var resultDiv = document.createElement('div');
                        resultDiv.innerText = result.display_name;
    
                        resultDiv.onclick = function () {
                            map.setView(latlng, 13);

                            currentMarker = L.marker(latlng).addTo(map)
                                .bindPopup(result.display_name)
                                .openPopup();

                            document.getElementById('route_button').style.display = 'block';

                            allMarkers.push(currentMarker);
                        };
                        
    
                        document.getElementById('search_results').appendChild(resultDiv);
                    });
                } else {
                    var resultsDiv = document.getElementById('search_results');
                    resultsDiv.innerHTML = '<p>No se encontraron colonias.</p>';
                }
            })
            .catch(error => {
                console.error("Error al realizar la búsqueda:", error);
                document.getElementById('search_results').innerHTML = '<p>Hubo un error al realizar la búsqueda.</p>';
            });
    };
    
    

    function LatLng(a) {
        const lat = a[1];  // latitud
        const lon =a[2];  // longitud

           
        const coordenadas = { lat: lat, lon: lon };
        return coordenadas;
    }
    var maxMaps = 4; 
    document.getElementById('route_button').onclick = function () {
        if (currentMarker) {
            var latlng = currentMarker.getLatLng(); 
            console.log(latlng);
            
    
            // Limpiar los mapas de la tabla
            for (let i = 1; i <= 4; i++) {
                const minimap = document.getElementById(`map${i}`);
                if (minimap) {
                    minimap.innerHTML = ''; // Elimina el contenido del mapa
                }
                
                const directions = document.getElementById(`directions${i}`);
                if (directions) {
                    directions.innerHTML = ''; // Elimina las direcciones
                }
            }
    
            // Crear un círculo en la posición actual
            currentCircle = L.circle(latlng, {
                color: 'red',
                fillColor: '#ff0000',
                fillOpacity: 0.3,
                radius: 1000
            }).addTo(map);
        
            allCircles.push(currentCircle);
            
            // Enviar coordenadas al servidor
            socket.emit('enviar_coordenadas', latlng);
            
            // Obtener cámaras cercanas
            socket.on('camaras_cercanas', function(camaras) {
                camaras.forEach(camara => {
                    if (camara.lat !== undefined && camara.lon !== undefined) {
                        const lat = camara.lat;
                        const lng = camara.lon;
    
                        if (lat && lng) {
                            let marker = L.marker([lat, lng], {
                                icon: L.icon({
                                    iconUrl: 'https://cdn-icons-png.freepik.com/512/8335/8335224.png',
                                    iconSize: [30, 30],
                                    iconAnchor: [15, 30]
                                })
                            }).addTo(map).bindPopup(`<b><a href="/camara">${camara.id}</a></b>`);
                            allMarkers.push(marker);
                        } else {
                            console.error("Cámara no tiene coordenadas válidas:", camara);
                        }
                    } else {
                        console.error("Cámara no tiene coordenadas válidas:", camara);
                    }
                });
            });
        
            // Definir destinos
            var destinos = [
                { lat: latlng.lat + 0.01, lng: latlng.lng + 0.01 },  
                { lat: latlng.lat - 0.01, lng: latlng.lng - 0.01 },  
                { lat: latlng.lat + 0.01, lng: latlng.lng - 0.01 },  
                { lat: latlng.lat - 0.01, lng: latlng.lng + 0.01 }   
            ];
    
            // Generar rutas para cada destino
            destinos.forEach((destino, index) => {
                generateRoute(latlng, destino, index + 1);
            });
        } else {
            console.log("No hay marcador actual.");
        }
    };
    
    function generateRoute(latlng, destino, mapIndex) {
        console.log("LatLng:", latlng);
        console.log("Destino:", destino);
        
        // ID de la tabla
        var table = document.getElementById('mapTable');
        
        // Limpiar el contenido de la tabla antes de agregar nuevos mapas
        table.innerHTML = '';
    
        // Crear el HTML para los nuevos mapas y direcciones
        for (let i = 1; i <= 4; i++) {
            var newRow = document.createElement('tr');
    
            // Crear una nueva celda para el mapa
            var newCell = document.createElement('td');
            newCell.id = "mapCell" + i;
            
            // Crear contenido para la celda
            var titleDiv = document.createElement('div');
            titleDiv.className = "texto-" + (i % 4 === 1 ? "verde" : i % 4 === 2 ? "rojo" : i % 4 === 3 ? "azul" : "naranja");
            titleDiv.innerText = "Ruta " + i; // Cambia esto según la descripción deseada
            newCell.appendChild(titleDiv);
    
            // Crear el div del mapa
            var mapDiv = document.createElement('div');
            mapDiv.className = 'minimap';
            mapDiv.id = "map" + i;
            mapDiv.style.width = '100%';
            mapDiv.style.height = '200px';
            newCell.appendChild(mapDiv);
    
            // Crear el div de las direcciones
            var directionsDiv = document.createElement('div');
            directionsDiv.id = "directions" + i;
            directionsDiv.className = 'directions';
            newCell.appendChild(directionsDiv);
            
            var fullscreenButton = document.createElement('button');
            fullscreenButton.innerText = "Pantalla Completa";
            fullscreenButton.className = "fullscreen-button"; // Aplicar la clase CSS
            fullscreenButton.onclick = function() {
                toggleFullscreen(mapDiv);
            };
            newCell.appendChild(fullscreenButton);
    
            // Agregar la celda a la fila
            newRow.appendChild(newCell);
            table.appendChild(newRow);
        }
    
        // Crear mapas para cada destino
        for (let i = 1; i <= 4; i++) {
            var destino = {
                lat: latlng.lat + (i % 2 === 0 ? -0.01 : 0.01),
                lng: latlng.lng + (i % 2 === 0 ? 0.01 : -0.01)
            };
            generateMap(latlng, destino, i);
        }
    }
    
    function generateMap(latlng, destino, mapIndex) {
        var mapDivId = "map" + mapIndex;
    
        // Crear un nuevo mapa
        var newMap = L.map(mapDivId).setView([latlng.lat, latlng.lng], 13);
    
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(newMap);
    
        // Crear control de enrutamiento
        var routingControl = L.Routing.control({
            waypoints: [
                L.latLng(latlng.lat, latlng.lng),
                L.latLng(destino.lat, destino.lng)
            ],
            routeWhileDragging: true,
         createMarker: function() { return null; },
         language: 'es' // Configura el idioma a español
        }).addTo(newMap);
    
        routingControl.on('routesfound', function (e) {
            var routes = e.routes;
            var instructions = routes[0].instructions;
    
            var directionsDiv = document.getElementById("directions" + mapIndex);
            directionsDiv.innerHTML = ''; // Limpiar instrucciones previas
            
            // Mostrar instrucciones
            // instructions.forEach(instruction => {
            //     var directionItem = document.createElement('div');
            //     directionItem.innerText = instruction.text;
            //     directionsDiv.appendChild(directionItem);
            // });
    
            var summary = routes[0].summary;
    
            socket.emit('ruta_cambiada', {
                distancia: summary.totalDistance,
                duracion: summary.totalTime,
                waypoints: routes[0].coordinates,
                calles: routes[0].instructions.map(instruction => instruction.text)
            });
        });
    }
    
    // Función para alternar pantalla completa
    function toggleFullscreen(element) {
        if (!document.fullscreenElement) {
            element.requestFullscreen().catch(err => {
                console.error(`Error al intentar activar pantalla completa: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
    
    

    document.getElementById('show_risk_areas_button').onclick = function () {
        clearMap();
        socket.emit('mostrar_zonas_riesgo');
    };

    socket.on('zonas_riesgo', function (zonas) {
        clearMap();
        zonas.forEach(function (zona) {
            
            let randomNumber = Math.floor(Math.random() * 101);
            const { nombre, lat, lng, riesgo } = zona;
            const color = obtenerColorRiesgo(riesgo);
        
            
            
            var circle = L.circle([lat, lng], {
                color: color,
                radius: 500,
                fillColor: color,
                fillOpacity: 0.5
            }).addTo(map);

            var marker = L.marker([lat, lng]).addTo(map)
                .bindPopup(`<b>${nombre}</b><br>Riesgo: ${riesgo}%`).openPopup();

            allCircles.push(circle);
            allMarkers.push(marker);
        });
    });

    function obtenerColorRiesgo(riesgo) {
        if (riesgo <= 30) return 'green';
        if (riesgo <= 60) return 'yellow';
        return 'red';
    }
});