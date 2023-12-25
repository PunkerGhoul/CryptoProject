function generateSecureRandomNumber(
  p,
  id_usuario_remitente,
  id_usuario_destinatario
) {
  // Verificar si el número aleatorio seguro ya existe en el almacenamiento local
  const existingValue = getItemFromLocalStorage(
    "secureRandomNumber" +
      "_" +
      id_usuario_remitente +
      "-" +
      id_usuario_destinatario
  );

  // Si el número existe y es un valor numérico válido, se devuelve
  if (existingValue && !isNaN(existingValue)) {
    return parseInt(existingValue);
  }

  // Generar continuamente números aleatorios hasta encontrar uno que sea primo
  while (true) {
    const randomBytes = CryptoJS.lib.WordArray.random(4);
    const randomNumber = randomBytes.words[0] % parseInt(p);

    // Verificar si el número aleatorio es primo
    if (isPrime(randomNumber)) {
      // Almacenar el número aleatorio seguro en el almacenamiento local
      setLocalStorageItem(
        "secureRandomNumber" +
          "_" +
          id_usuario_remitente +
          "-" +
          id_usuario_destinatario,
        randomNumber.toString()
      );
      return randomNumber;
    }
  }
}

function isPrime(number) {
  // Caso especial: números menores o iguales a 1 no son primos
  if (number <= 1) {
    return false;
  }
  // Caso especial: 2 es el único número par primo
  else if (number === 2) {
    return true;
  }
  // Caso especial: números pares mayores que 2 no son primos
  else if (number % 2 === 0) {
    return false;
  }

  // Iteramos por los números impares hasta la mitad de 'number'
  for (let i = 3; i <= Math.floor(number / 2); i += 2) {
    if (number % i === 0) {
      // Si encontramos un divisor, el número no es primo
      return false;
    }
  }

  // Si no se encontraron divisores, el número es primo
  return true;
}

function setLocalStorageItem(name, value) {
  localStorage.setItem(name, value);
}

function getItemFromLocalStorage(name) {
  return localStorage.getItem(name) || null;
}

// Obtener el elemento del input
const inputElement = document.querySelector('input[name="claveSesion"]');
// Obtener el valor seleccionado de la caja desplegable
const id_usuario_remitente = id_usuario; // Asignar el valor de id_usuario desde el HTML
const usernameSelect = document.getElementById("usernameSelect");

// Función para iniciar la comunicación
function iniciarComunicacion() {
  const selectedUserId = usernameSelect.value;
  const confirmationKey = `confirmation_${selectedUserId}`;
  const isConfirmationDone = localStorage.getItem(confirmationKey);

  if (!isConfirmationDone) {
    confirmation(usernameSelect, confirmationKey);
  } else {
    obtenerRemitentep(selectedUserId);
    obtenerDestinatariop(selectedUserId);
  }
}

// Ejecutar la función al cargar la página
window.addEventListener("load", iniciarComunicacion);

// Ejecutar la función cuando se cambia la opción de usuario
usernameSelect.addEventListener("change", iniciarComunicacion);

function obtenerRemitentep(selectedUserId) {
  fetch(
    `/api/get_conv_p_pub_key?id_usuario_remitente=${selectedUserId}&id_usuario_destinatario=${id_usuario_remitente}`,
    {
      method: "GET",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      try {
        if ("p" in data && "pub_key" in data) {
          const p = BigInt(data.p);
          const k = BigInt(data.k);
          let pub_key = BigInt(data.pub_key);

          if (pub_key === 0n) {
            const secureRandomNumber = BigInt(
              generateSecureRandomNumber(
                p,
                id_usuario_remitente,
                selectedUserId
              )
            );
            pub_key = k ** secureRandomNumber % p;

            fetch(
              `/api/set_pubkey?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}&pub_key=${pub_key}`,
              {
                method: "GET",
              }
            )
              .then((response) => response.json())
              .then((data) => {
                console.log(data.message);
                Swal.fire(
                  "¡Llave pública establecida!",
                  "Tu llave pública es " + pub_key.toString(),
                  "OK"
                );
                //alert(`Tu llave pública es: ${pub_key.toString()}`);
              })
              .catch((error) => {
                console.error("Error al establecer la llave pública:", error);
              });

            return;
          }

          inputElement.value = pub_key.toString();
        } else {
          if (id_usuario_remitente != selectedUserId) {
            fetch(
              `/api/gen_conversation_keys?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}`,
              {
                method: "GET",
              }
            )
              .then((response) => response.json())
              .then((data) => {
                try {
                  const p = BigInt(data.p);
                  const k = BigInt(data.k);
                  const secureRandomNumber = BigInt(
                    generateSecureRandomNumber(
                      p,
                      id_usuario_remitente,
                      selectedUserId
                    )
                  );
                  const pub_key = k ** secureRandomNumber % p;

                  fetch(
                    `/api/set_pubkey?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}&pub_key=${pub_key}`,
                    {
                      method: "GET",
                    }
                  )
                    .then((response) => response.json())
                    .then((data) => {
                      console.log(data.message);
                      Swal.fire(
                        "¡Llave pública establecida!",
                        "Tu llave pública es " + pub_key.toString(),
                        "OK"
                      );
                      //alert(`Tu llave pública es: ${pub_key.toString()}`);
                    })
                    .catch((error) => {
                      console.error(
                        "Error al establecer la llave pública:",
                        error
                      );
                    });

                  console.log(pub_key);
                } catch (error) {
                  console.error("Error al generar las claves:", error);
                  inputElement.value = "";
                }
              })
              .catch((error) => {
                console.error("Error al generar las claves:", error);
              });
            inputElement.value = "";
          }
        }
      } catch {
        inputElement.value = "";
      }
    })
    .catch((error) => {
      console.error("Error al obtener el valor de p:", error);
    });
}

function obtenerDestinatariop(selectedUserId) {
  fetch(
    `/api/get_conv_p_pub_key?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}`,
    {
      method: "GET",
    }
  )
    .then((response) => response.json())
    .then((data) => {
      try {
        if ("p" in data && "pub_key" in data) {
          const p = BigInt(data.p);
          const pub_key = BigInt(data.pub_key);

          if (pub_key === 0n) {
            alert("El usuario seleccionado no ha establecido su llave pública");
            Swal.fire({
              icon: "error",
              title: "Hey!! Primero Consentimiento Mutuo",
              text: "Con quien quieres hablar no esta disponible aún",
              footer:
                "Vuelve a intentarlo más tarde, cuando el usuario quiera hablar contigo",
            });
            return;
          }

          const secureRandomNumber = BigInt(
            generateSecureRandomNumber(p, id_usuario_remitente, selectedUserId)
          );
          const result = pub_key ** secureRandomNumber % p;
          inputElement.value = result.toString();
        } else {
          if (id_usuario_remitente === selectedUserId) {
            //alert("No puedes establecer una comunicación contigo mismo");
            Swal.fire({
              icon: "error",
              title: "Oops...",
              text: "No puedes establecer una comunicación contigo mismo",
              footer:
                "Selecciona a otro usuario para establecer una comunicación",
            });
          } else {
            fetch(
              `/api/gen_conversation_keys?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}`,
              {
                method: "GET",
              }
            )
              .then((response) => response.json())
              .then((data) => {
                try {
                  const p = BigInt(data.p);
                  const k = BigInt(data.k);
                  const secureRandomNumber = BigInt(
                    generateSecureRandomNumber(
                      p,
                      id_usuario_remitente,
                      selectedUserId
                    )
                  );
                  const pub_key = k ** secureRandomNumber % p;

                  fetch(
                    `/api/set_pubkey?id_usuario_remitente=${id_usuario_remitente}&id_usuario_destinatario=${selectedUserId}&pub_key=${pub_key}`,
                    {
                      method: "GET",
                    }
                  )
                    .then((response) => response.json())
                    .then((data) => {
                      console.log(data.message);
                      Swal.fire(
                        "¡Llave pública establecida!",
                        "Tu llave pública es " + pub_key.toString(),
                        "OK"
                      );
                      //alert(`Tu llave pública es: ${pub_key.toString()}`);
                    })
                    .catch((error) => {
                      console.error(
                        "Error al establecer la llave pública:",
                        error
                      );
                    });

                  console.log(pub_key);
                } catch (error) {
                  console.error("Error al generar las claves:", error);
                  inputElement.value = "";
                }
              })
              .catch((error) => {
                console.error("Error al generar las claves:", error);
              });
          }
        }
      } catch {
        inputElement.value = "";
      }
    })
    .catch((error) => {
      console.error("Error al obtener el valor de p:", error);
    });
}

function confirmation(usernameSelect, confirmationKey) {
  Swal.fire({
    title: "¿Estás seguro?",
    text: `¿Deseas establecer una comunicación con ${
      usernameSelect.options[usernameSelect.selectedIndex].text
    }?`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#3085d6",
    cancelButtonColor: "#d33",
    confirmButtonText: "Yes, delete it!",
  }).then((result) => {
    if (result.isConfirmed) {
      // La confirmación ha sido aceptada, guardar el estado en localStorage
      localStorage.setItem(confirmationKey, "true");
      Swal.fire(
        "Has aceptado establecer comunicación!",
        "Debes esperar a que " +
          usernameSelect.options[usernameSelect.selectedIndex].text +
          " acepte la comunicación",
        "OK"
      );
    } else {
      // Si el usuario no confirma, resetear el valor del select
      usernameSelect.value = "";
      inputElement.value = "";
    }
  });
  /*
  if (
    confirm(
      `¿Deseas establecer una comunicación con ${
        usernameSelect.options[usernameSelect.selectedIndex].text
      }?`
    )
  ) {
    // La confirmación ha sido aceptada, guardar el estado en localStorage
    localStorage.setItem(confirmationKey, "true");
  } else {
    // Si el usuario no confirma, resetear el valor del select
    usernameSelect.value = "";
    inputElement.value = "";
  }*/
}

/* Funcionamiento del codigo:
Se importa la biblioteca CryptoJS. Luego, se crea la función llamada generateSecureRandomNumber(). 
Dentro de esta función, se generan 4 bytes de datos aleatorios utilizando CryptoJS.lib.WordArray.random(4). 
Luego, se toma el primer valor de randomBytes y se reduce al rango de 0 a 999 utilizando el operador módulo %. 
Finalmente, se retorna a el número generado.
*/
