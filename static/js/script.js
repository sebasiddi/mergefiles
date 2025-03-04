document.addEventListener("DOMContentLoaded", function() {
  let dropArea = document.getElementById("drop-area");
  let fileInput = document.getElementById("fileInput");
  let fileNameDisplay = document.getElementById("file-name");
  let dropText = document.getElementById("drop-text");

  // Extensiones de audio permitidas
  const audioExtensions = ["mp3", "wav", "ogg", "flac", "aac", "m4a"];

  // Cuando se hace clic en el área, abrir el selector de archivos
  dropArea.addEventListener("click", () => fileInput.click());

  // Resaltar área cuando el archivo se arrastra encima
  dropArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropArea.classList.add("highlight");
  });

  dropArea.addEventListener("dragleave", () => {
      dropArea.classList.remove("highlight");
  });

  // Manejar el archivo soltado
  dropArea.addEventListener("drop", (e) => {
      e.preventDefault();
      dropArea.classList.remove("highlight");

      let files = e.dataTransfer.files;
      if (files.length > 0) {
          validarArchivo(files[0]);
      }
  });

  // Mostrar el nombre del archivo cuando se selecciona manualmente
  fileInput.addEventListener("change", function() {
      if (fileInput.files.length > 0) {
          validarArchivo(fileInput.files[0]);
      }
  });

  function validarArchivo(file) {
      let extension = file.name.split(".").pop().toLowerCase();
      if (audioExtensions.includes(extension)) {
          mostrarNombreArchivo(file.name);
      } else {
          alert("Por favor, selecciona un archivo de audio válido.");
          fileInput.value = ""; // Limpia el input
          fileNameDisplay.textContent = "";
          dropText.textContent = "Arrastra tu archivo aquí o haz clic para seleccionarlo";
      }
  }

  function mostrarNombreArchivo(nombre) {
      fileNameDisplay.textContent = `Archivo seleccionado: ${nombre}`;
      dropText.textContent = `${nombre} listo para subir`;
  }
});
