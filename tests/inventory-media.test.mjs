import test from 'node:test';
import assert from 'node:assert/strict';
import {imageUrls} from '../src/crm-logic.mjs';
test('Sheet Cloudinary photos are used for property cards',()=>{
 const row={cloudinary_image_urls:['https://res.cloudinary.com/dcvwsclyc/image/upload/v1/photo_1.jpg','https://res.cloudinary.com/dcvwsclyc/image/upload/v1/photo_2.jpg']};
 assert.equal(imageUrls(row).length,2);
 assert.deepEqual(imageUrls({cloudinary_image_urls:[]}),[]);
 assert.deepEqual(imageUrls({photos:['https://example.com/authorized.jpg']}),['https://example.com/authorized.jpg']);
});
