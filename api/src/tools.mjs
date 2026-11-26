// Emulates the Claude "Google Sheets" / "Google Drive" connector tools the app calls through window.claude mcp.
// Same tool names, same input fields, same {payload} result shape, so the app code needs no change.
//   Google Sheets: get_values, update_values, append_values, update_spreadsheet, get_spreadsheet, batch_clear_values
//   Google Drive:  search_files (Drive v2-style query: parentId / title), create_file
export async function callTool({ server, tool, input = {} }, { gapi, guard }) {
  await guard.check(server, tool, input);
  if (server === 'Google Sheets') {
    const id = input.spreadsheetId;
    switch (tool) {
      case 'get_values': return { payload: { values: (await gapi.getValues(id, input.range)).values || [] } };
      case 'update_values': return { payload: await gapi.updateValues(id, input.range, input.values || []) };
      case 'append_values': return { payload: await gapi.appendValues(id, input.range, input.values || []) };
      case 'update_spreadsheet': return { payload: await gapi.batchUpdate(id, input.requests || []) };
      case 'batch_clear_values': return { payload: await gapi.batchClear(id, input.ranges || []) };
      case 'get_spreadsheet': {
        const f = Array.isArray(input.fields) ? input.fields.join(',') : input.fields || '';
        return { payload: await gapi.getSpreadsheet(id, f) };
      }
    }
  }
  if (server === 'Google Drive') {
    if (tool === 'search_files') {
      const q = String(input.query || '')
        .replace(/\bparentId\s*=\s*'((?:[^'\\]|\\.)*)'/g, "'$1' in parents")
        .replace(/\btitle\s*(=|contains)\s*/g, 'name $1 ');
      const r = await gapi.driveSearch(q, input.pageSize || 10);
      return { payload: { files: (r.files || []).map((f) => ({ id: f.id, title: f.name, parents: f.parents })) } };
    }
    if (tool === 'create_file') {
      const r = await gapi.driveCreate({ name: input.title, mimeType: input.contentMimeType, parents: input.parentId ? [input.parentId] : undefined });
      return { payload: { id: r.id, title: r.name } };
    }
  }
  throw { code: 'tool_error', message: 'Unsupported tool: ' + server + ' / ' + tool };
}
