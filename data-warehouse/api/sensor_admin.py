from fastapi import APIRouter, HTTPException, Depends
from app.utils.csv_store import read_all, write_all, append_row
from app import auth


router = APIRouter(prefix='/api/sensor', tags=['Sensors'])


@router.get('/admin/sensors')
def list_rows():
return read_all()


@router.post('/')
def create_row(payload: dict, user=Depends(auth.get_current_active_user)):
# Optionally restrict: if user.role == 'user', tag owner_id
row = {
'Sensor ID': payload['sensor_id'],
'Start Timestamp': payload['start_timestamp'],
'End Timestamp': payload['end_timestamp'],
'Value': str(payload['value']),
'Unit': payload['unit'],
}
out = append_row(row)
return { 'message': 'created', 'id': out['id'] }


@router.put('/{row_id}')
def update_row(row_id: str, payload: dict, user=Depends(auth.get_current_active_user)):
rows = read_all()
updated = False
for r in rows:
if r['id'] == row_id:
r['Sensor ID'] = payload['sensor_id']
r['Start Timestamp'] = payload['start_timestamp']
r['End Timestamp'] = payload['end_timestamp']
r['Value'] = str(payload['value'])
r['Unit'] = payload['unit']
updated = True
break
if not updated:
raise HTTPException(404, 'Row not found')
write_all(rows)
return { 'message': 'updated' }


@router.delete('/{row_id}')
def delete_row(row_id: str, user=Depends(auth.get_current_active_user)):
rows = read_all()
new_rows = [r for r in rows if r['id'] != row_id]
if len(new_rows) == len(rows):
raise HTTPException(404, 'Row not found')
write_all(new_rows)
return { 'message': 'deleted' }