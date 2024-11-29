<?php
// Проверьте, что файл класса HLRLookupClient существует
if (!file_exists('HLRLookupClient.class.php')) {
    http_response_code(500);
    echo json_encode(['error' => 'Файл HLRLookupClient.class.php не найден']);
    exit;
}

// Подключаем класс HLRLookupClient
include('HLRLookupClient.class.php');

// Настройка API-клиента
$client = new HLRLookupClient(
    'api.key',               
    'secret.key', 
    __DIR__ . '/hlr_lookup.log'      // Лог-файл
);

// Логирование запросов для отладки
file_put_contents('debug.log', print_r([
    'method' => $_SERVER['REQUEST_METHOD'],
    'path' => $_GET['action'] ?? null,
    'data' => json_decode(file_get_contents("php://input"), true)
], true), FILE_APPEND);

// Получение параметров запроса
$requestMethod = $_SERVER['REQUEST_METHOD'];
$requestPath = $_GET['action'] ?? null;
$inputData = json_decode(file_get_contents("php://input"), true);

// Функция для отправки ответа
function sendResponse($status, $data) {
    http_response_code($status);
    echo json_encode($data);
    exit;
}

// Обработка запросов
try {
    if ($requestMethod === 'GET' && $requestPath === 'auth-test') {
        // Проверка аутентификации
        $response = $client->get('/auth-test');
        sendResponse($response->httpStatusCode, json_decode($response->responseBody, true));
    } elseif ($requestMethod === 'POST' && $requestPath === 'hlr-lookup') {
        // Проверка HLR
        if (!isset($inputData['msisdn'])) {
            sendResponse(400, ['error' => 'Номер телефона (msisdn) обязателен']);
        }
        $response = $client->post('/hlr-lookup', ['msisdn' => $inputData['msisdn']]);
        sendResponse($response->httpStatusCode, json_decode($response->responseBody, true));
    } elseif ($requestMethod === 'POST' && $requestPath === 'nt-lookup') {
        // Проверка NT
        if (!isset($inputData['number'])) {
            sendResponse(400, ['error' => 'Номер (number) обязателен']);
        }
        $response = $client->post('/nt-lookup', ['number' => $inputData['number']]);
        sendResponse($response->httpStatusCode, json_decode($response->responseBody, true));
    } elseif ($requestMethod === 'POST' && $requestPath === 'mnp-lookup') {
        // Проверка MNP
        if (!isset($inputData['msisdn'])) {
            sendResponse(400, ['error' => 'Номер телефона (msisdn) обязателен']);
        }
        $response = $client->post('/mnp-lookup', ['msisdn' => $inputData['msisdn']]);
        sendResponse($response->httpStatusCode, json_decode($response->responseBody, true));
    } elseif ($requestMethod === 'POST' && $requestPath === 'validate-number') {
        // Проверка номера (пример через nt-lookup)
        if (!isset($inputData['number'])) {
            sendResponse(400, ['error' => 'Номер (number) обязателен']);
        }
        $response = $client->post('/nt-lookup', ['number' => $inputData['number']]);
        sendResponse($response->httpStatusCode, json_decode($response->responseBody, true));
    } else {
        sendResponse(404, ['error' => 'Неподдерживаемое действие']);
    }
} catch (Exception $e) {
    sendResponse(500, ['error' => 'Ошибка сервера', 'details' => $e->getMessage()]);
}
