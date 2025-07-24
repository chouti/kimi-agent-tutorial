// ROT13解码函数
function rot13(str) {
    return str.replace(/[A-Za-z]/g, function(char) {
        var code = char.charCodeAt(0);
        if (code >= 65 && code <= 90) {
            // 大写字母 A-Z
            return String.fromCharCode(((code - 65 + 13) % 26) + 65);
        } else if (code >= 97 && code <= 122) {
            // 小写字母 a-z
            return String.fromCharCode(((code - 97 + 13) % 26) + 97);
        }
        return char;
    });
}

// 需要解码的字符串
const encodedString = 'Pbatenghyngvbaf ba ohvyqvat n pbqr-rqvgvat ntrag!';

// 解码并打印结果
const decodedString = rot13(encodedString);
console.log('解码后的字符串:', decodedString);