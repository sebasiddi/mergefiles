document.addEventListener("DOMContentLoaded", function() {
  let dropArea = document.getElementById("drop-area");
  let fileInput = document.getElementById("fileInput");
  let fileNameDisplay = document.getElementById("file-name");
  let dropText = document.getElementById("drop-text");

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
          fileInput.files = files;
          mostrarNombreArchivo(files[0].name);
      }
  });

  // Mostrar el nombre del archivo cuando se selecciona manualmente
  fileInput.addEventListener("change", function() {
      if (fileInput.files.length > 0) {
          mostrarNombreArchivo(fileInput.files[0].name);
      }
  });

  function mostrarNombreArchivo(nombre) {
      fileNameDisplay.textContent = `Archivo seleccionado: ${nombre}`;
      dropText.textContent = `${nombre} listo para subir`;
  }
});
